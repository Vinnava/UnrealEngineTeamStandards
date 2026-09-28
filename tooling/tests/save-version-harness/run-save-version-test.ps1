<#
.SYNOPSIS
    Proves the save versioning in standard section 24 by building a game several times over and
    loading each build's saves in the next. Exit code 0 means every check passed.

.DESCRIPTION
    Run it after changing section 24 or its code, and on every engine upgrade (standard 22.2). One
    scratch project is rebuilt as successive builds of the same game, and its Saved/SaveGames folder
    carries over between them exactly as a player's does:
      0  a build from before versioning writes a save - and the engine facts in 16.3 are checked on it;
      1  the 24.3 scaffolding lands: the old save loads, a format-0 save is written;
      2  one version is appended: both older saves migrate once, duplicates behave as 16.3 says, and
         a format-1 save is written;
      1  the build is rolled back: the format-1 save is refused and never overwritten.
    Then two mistakes 24.5 forbids are built on purpose, and each must do the damage 24.5 predicts -
    a harness that cannot see a mistake proves nothing about the rule against it.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tooling\tests\save-version-harness\run-save-version-test.ps1
#>
param(
    [string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.7",
    # Kept short on purpose: UBT refuses action paths over 260 characters, and fails outright if the
    # project sits at a drive root.
    [string]$WorkDir = (Join-Path $env:TEMP "ues-sv")
)

$ErrorActionPreference = "Stop"
$harness = $PSScriptRoot
$editor = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$build = Join-Path $EngineRoot "Engine\Build\BatchFiles\Build.bat"
$project = Join-Path $WorkDir "SaveCheck.uproject"
$headless = @("-unattended", "-nopause", "-nosplash", "-nullrhi", "-stdout")
$failures = New-Object System.Collections.Generic.List[string]

function Step([string]$text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Check([bool]$ok, [string]$what) {
    if ($ok) { Write-Host "   ok    $what" -ForegroundColor Green }
    else { Write-Host "   FAIL  $what" -ForegroundColor Red; $failures.Add($what) }
}

function Build-Game([int]$phase, [int]$mutation, [string]$name) {
    Set-Content -Encoding ascii (Join-Path $WorkDir "Source\SaveCheck\HarnessPhase.h") @(
        "#pragma once", "#define SAVE_CHECK_PHASE $phase", "#define SAVE_CHECK_MUTATION $mutation")
    $log = Join-Path $WorkDir "build-$name.log"
    & $build SaveCheckEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReload *> $log
    $built = $LASTEXITCODE -eq 0
    Check $built "build '$name' compiles"
    $ours = Get-Content $log | Where-Object { $_ -match '\\SaveCheck\\.*\.(h|cpp).*: (warning|error)' }
    Check (-not $ours) "no compiler warning in the harness in build '$name'"
    if (-not $built) { Write-Host "`nBuild failed - see $log" -ForegroundColor Red; exit 1 }
}

# Runs one commandlet step and forwards its SAVECHECK lines as checks. The exit code is not the verdict:
# the loader logs a refusal as an Error by design, and any Error makes the commandlet exit 1. A step
# passes when the commandlet reports no failure and nothing but LogGameSave logged an error - an engine
# ensure or check still fails it.
function Run-Step([string]$step) {
    $log = Join-Path $WorkDir "run-$step.log"
    & $editor $project -run=SaveCheck "-step=$step" @headless *> $log
    $code = $LASTEXITCODE
    $text = Get-Content $log
    $lines = $text | Where-Object { $_ -match 'SAVECHECK (ok  |FAIL) ' } |
        ForEach-Object { ($_ -replace '^.*SAVECHECK ', '').Trim() } | Select-Object -Unique
    foreach ($line in $lines) { Check ($line -match '^ok ') ($line -replace '^(ok|FAIL)\s+', '') }
    $foreign = @($text | Where-Object { $_ -match ': (Error|Fatal):' -and $_ -notmatch 'LogGameSave: Error:' })
    $clean = ($text -match 'SAVECHECK done, 0 failure\(s\)') -and $foreign.Count -eq 0
    return @{ Code = $code; Clean = [bool]$clean; Log = $log; Checks = @($lines).Count }
}

Step "Preparing $WorkDir"
if (Test-Path $WorkDir) { Remove-Item -Recurse -Force $WorkDir }
Copy-Item -Recurse $harness $WorkDir

Step "Build 0 - shipped before versioning existed"
Build-Game 0 0 "phase0"
$r = Run-Step "unversioned"
Check ($r.Clean -and $r.Checks -eq 4) "step passes with all 4 checks reported"

Step "Build 1 - the 24.3 scaffolding lands"
Build-Game 1 0 "phase1"
$r = Run-Step "phase1"
Check ($r.Clean -and $r.Checks -eq 6) "step passes with all 6 checks reported"

Step "Build 2 - HealthIsFraction appended"
Build-Game 2 0 "phase2"
$r = Run-Step "phase2"
Check ($r.Clean -and $r.Checks -eq 17) "step passes with all 17 checks reported"

Step "Build 1 again - rolled back"
Build-Game 1 0 "rollback"
$r = Run-Step "rollback"
Check ($r.Clean -and $r.Checks -eq 4) "step passes with all 4 checks reported"

Step "Mutation - the GUID regenerated after saves shipped"
Build-Game 2 1 "newguid"
$r = Run-Step "newguid"
Check ($r.Clean -and $r.Checks -eq 2) "the double migration 24.5 predicts happened"

Step "Mutation - CustomVer without UsingCustomVersion"
Build-Game 2 2 "skipusing"
$r = Run-Step "skipusing"
Check ($r.Code -ne 0) "saving stops the process (exit $($r.Code))"
Check (Select-String -Path $r.Log -Pattern "IsLoading\(\) \|\| CustomVersion" -Quiet) "at the engine's check in CustomVer (16.3)"

if ($failures.Count) {
    Write-Host "`n$($failures.Count) check(s) failed. Logs are in $WorkDir" -ForegroundColor Red
    exit 1
}
Write-Host "`nAll save versioning checks passed." -ForegroundColor Green
exit 0

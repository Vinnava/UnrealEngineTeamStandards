<#
.SYNOPSIS
    Compiles tooling/Validators against an installed engine and proves, in a headless editor, that
    they catch exactly what the standard says they catch. Exit code 0 means every check passed.

.DESCRIPTION
    Run it after changing a validator, and on every engine upgrade (standard 22.2). It:
      1. builds the validators in a scratch project with no PCH and no unity build, and fails on any
         warning in them;
      2. creates assets built to pass, to fail, or to warn (make_assets.py);
      3. runs the DataValidation commandlet - the same command CI runs - and checks every finding,
         the absence of engine ensures, and the exit code;
      4. deletes the failing assets, validates again, and checks that a warning alone exits 0.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File tooling\tests\validator-harness\run-validator-test.ps1
#>
param(
    [string]$EngineRoot = "C:\Program Files\Epic Games\UE_5.7",
    # Kept short on purpose: UBT refuses action paths over 260 characters, and fails outright if the
    # project sits at a drive root.
    [string]$WorkDir = (Join-Path $env:TEMP "ues-vh")
)

$ErrorActionPreference = "Stop"
$harness = $PSScriptRoot
$validators = Join-Path $harness "..\..\Validators"
$editor = Join-Path $EngineRoot "Engine\Binaries\Win64\UnrealEditor-Cmd.exe"
$build = Join-Path $EngineRoot "Engine\Build\BatchFiles\Build.bat"
$project = Join-Path $WorkDir "NamingCheck.uproject"
$headless = @("-unattended", "-nopause", "-nosplash", "-nullrhi", "-stdout")
$failures = New-Object System.Collections.Generic.List[string]

function Step([string]$text) { Write-Host "`n== $text" -ForegroundColor Cyan }
function Check([bool]$ok, [string]$what) {
    if ($ok) { Write-Host "   ok    $what" -ForegroundColor Green }
    else { Write-Host "   FAIL  $what" -ForegroundColor Red; $failures.Add($what) }
}
function Findings([string]$log) {
    # The commandlet prints every finding twice - once as it happens, once in its closing summary
    # behind a "LogInit: Display:" prefix - so strip both prefixes before de-duplicating
    Get-Content $log | Where-Object { $_ -match "\(standard \d|no prefix rule" } |
        ForEach-Object { ($_ -replace '^\[.*?\]\[.*?\]', '' -replace '^LogInit: Display: ', '').Trim() } |
        Select-Object -Unique
}

Step "Preparing $WorkDir"
if (Test-Path $WorkDir) { Remove-Item -Recurse -Force $WorkDir }
Copy-Item -Recurse $harness $WorkDir
Copy-Item (Join-Path $validators "*.h"), (Join-Path $validators "*.cpp") (Join-Path $WorkDir "Source\NamingCheckEditor")

Step "Building the validators (no PCH, no unity)"
& $build NamingCheckEditor Win64 Development "-Project=$project" -WaitMutex -NoHotReload *> (Join-Path $WorkDir "build.log")
Check ($LASTEXITCODE -eq 0) "the validators compile"
$ours = Get-Content (Join-Path $WorkDir "build.log") |
    Where-Object { $_ -match '(ProjectValidatorBase|AssetNamingValidator|AssetContentValidator)\.(h|cpp).*: (warning|error)' }
Check (-not $ours) "no compiler warning in any validator file"
if ($failures.Count) { Write-Host "`nBuild failed - see $WorkDir\build.log" -ForegroundColor Red; exit 1 }

Step "Creating test assets"
& $editor $project -run=pythonscript "-script=$(Join-Path $WorkDir 'make_assets.py')" @headless *> (Join-Path $WorkDir "make.log")
Check ($LASTEXITCODE -eq 0) "the asset script runs"
$created = @(Get-ChildItem (Join-Path $WorkDir "Content\_Test\*.uasset") -ErrorAction SilentlyContinue).Count
Check ($created -eq 11) "11 test assets created under the content root (found $created)"

Step "Validating everything - the command CI runs"
$log = Join-Path $WorkDir "validate-all.log"
& $editor $project -run=DataValidation @headless *> $log
Check ($LASTEXITCODE -ne 0) "failing assets make the commandlet exit non-zero (14.5)"
$found = Findings $log
$expected = [ordered]@{
    "BP_Main needs its 7.2 role prefix"       = "'BP_Main' must start with 'BP_GM_' or 'BP_TEMP_'"
    "BP_TEMP_ragdoll is not PascalCase"       = "'BP_TEMP_ragdoll' needs a PascalCase name after 'BP_TEMP_'"
    "T_NotPow2 cannot stream"                 = "'T_NotPow2' is 300x200, which can never stream"
    "T_Big is over the configured budget"     = "'T_Big' is 1024x1024, over the 512 budget"
    "SM_Sphere has no LODs"                   = "'SM_Sphere' has 960 triangles, one LOD, and Nanite off"
    "an unmapped type warns"                  = "'Unmapped' is a 'SubsurfaceProfile', which has no prefix rule yet"
}
foreach ($case in $expected.GetEnumerator()) {
    Check ([bool]($found | Where-Object { $_ -like "*$($case.Value)*" })) $case.Key
}
$errors = @($found | Where-Object { $_ -match 'Error:' }).Count
Check ($errors -eq 5) "exactly 5 errors, no false positives (found $errors)"
Check (-not ($found | Where-Object { $_ -match "BP_whatever" })) "nothing outside the content root is checked"
Check (-not ($found | Where-Object { $_ -match "MacroHelpers" })) "a macro library passes - 7.1 gives it no prefix"
Check (-not ($found | Where-Object { $_ -match "_C'" })) "a Blueprint's generated class is not reported twice (16.9)"
Check (-not (Select-String -Path $log -Pattern "Ensure condition|did not return a validation result" -Quiet)) "no engine ensure - every accepted asset gets a verdict (16.9)"

Step "Validating with the failing assets removed"
foreach ($bad in "BP_Main", "BP_TEMP_ragdoll", "T_NotPow2", "T_Big", "SM_Sphere") {
    Remove-Item (Join-Path $WorkDir "Content\_Test\$bad.uasset")
}
$log = Join-Path $WorkDir "validate-good.log"
& $editor $project -run=DataValidation @headless *> $log
Check ($LASTEXITCODE -eq 0) "a warning alone does not fail CI"
$found = Findings $log
Check (-not ($found | Where-Object { $_ -match 'Error:' })) "no errors on the passing assets"
Check ([bool]($found | Where-Object { $_ -match "no prefix rule yet" })) "the warning is still reported"

if ($failures.Count) {
    Write-Host "`n$($failures.Count) check(s) failed. Logs are in $WorkDir" -ForegroundColor Red
    exit 1
}
Write-Host "`nAll validator checks passed." -ForegroundColor Green
exit 0

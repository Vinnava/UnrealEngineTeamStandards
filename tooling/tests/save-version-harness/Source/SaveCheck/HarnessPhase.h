#pragma once

// Rewritten by run-save-version-test.ps1 before each build. Each phase stands for one build of a game:
//   0  shipped before versioning existed - no registration, nothing recorded on load
//   1  the section 24 scaffolding added; the enum holds only BeforeCustomVersionWasAdded
//   2  one version appended - HealthIsFraction, with its migration
// A mutation is a mistake 24.5 forbids, built on purpose to prove the harness sees what it breaks:
//   1  the GUID regenerated after saves shipped
//   2  CustomVer read without UsingCustomVersion first
#define SAVE_CHECK_PHASE 2
#define SAVE_CHECK_MUTATION 0

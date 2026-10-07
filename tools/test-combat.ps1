param(
    [string]$EngineRoot = 'C:/Program Files/Epic Games/UE_5.8',
    [switch]$SkipBuild,
    [int]$TimeoutSeconds = 240
)
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/combat-process.ps1"
$projectRoot = Split-Path $PSScriptRoot -Parent
$projectFile = Join-Path $projectRoot 'Constellation.uproject'
$logDir = Join-Path $projectRoot 'Saved/Logs'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
if (-not $SkipBuild) {
    & (Join-Path $EngineRoot 'Engine/Build/BatchFiles/Build.bat') ConstellationEditor Win64 Development "-Project=$projectFile" -WaitMutex -NoHotReloadFromIDE -NoUBTMakefiles -gather *> (Join-Path $logDir 'Combat-build.log')
    if ($LASTEXITCODE -ne 0) { throw 'Editor build failed. See Saved/Logs/Combat-build.log' }
}
$testLog = Join-Path $logDir 'Combat-tests.log'
$arguments = @(
    ('"{0}"' -f $projectFile), '/Engine/Maps/Entry', '-unattended', '-nop4', '-nosplash', '-NullRHI',
    '"-ExecCmds=Automation RunTests Constellation.CombatCore"',
    '"-TestExit=Automation Test Queue Empty"', ('"-abslog={0}"' -f $testLog)
)
$process = Start-Process -FilePath (Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe') -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDir 'Combat-tests-console.log') -RedirectStandardError (Join-Path $logDir 'Combat-tests-stderr.log')
try { $exitCode=Wait-CombatProcess -Process $process -TimeoutSeconds $TimeoutSeconds }
finally { $process.Dispose() }
$contents = Get-Content -LiteralPath $testLog -Raw
$expected = @('HitLedger','DamageAndDeath','InvalidAction','MontageLifecycle','CostCooldownAndValidation','NaturalMontageCompletion','ReentrantCostCancellation','AutomaticWindowsAndOcclusion','ReentrantReplacement','BehaviorTreeAbortAndDestroy','CameraRelativeMovement','TargetLockLifecycle','LocomotionAndAttackRecovery','MouseCameraInput','ProjectControlDefaults','BufferedFollowUp','BufferedCancellationAndReplacement','BufferedResourceAndValidation','StaminaRecovery','HitReactionLifecycle','HitDuringHandoff','DodgeLifecycle','DodgeRestrictions','DodgeReentrantStart','PatternSelection','PatternCommittedInterruption','EncounterLifecycle','EncounterSightAndNavigationFailure','EditorCharacterValidation','EditorCharacterReport','ResourceLimits','WorkbenchCloneIsolation','WorkbenchDraftValidation','WorkbenchPresetAndRestart','ActionObservation','DamageObservation','WorkbenchTuningReport','WorkbenchInputWindow','DodgeCancelWindow','DodgeCancelReentry','UltimateResource','UltimateCommitReentry','SpecialSlots','SpecialSlotClone','RadialOcclusion','ActionDashLifecycle','ActionDashCollision','AuthoredHitWindows','EncounterConcurrency','EncounterFailureCleanup','ProjectCarryPriority','EncounterSceneSignal')
$missing = @($expected | Where-Object { $contents -notmatch ('Test Completed\. Result=\{Success\} Name=\{' + [regex]::Escape($_) + '\}') })
if ($exitCode -ne 0 -or $contents -match 'LogAutomationController: Error:|Fatal error:|Assertion failed:' -or $missing.Count) {
    throw "Combat tests failed or incomplete. Exit code: $exitCode. Missing successful tests: $($missing -join ', '). See $testLog"
}
Write-Output "PASS: $($expected.Count) combat tests. $testLog"

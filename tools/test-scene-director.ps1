param([string]$EngineRoot='C:/Program Files/Epic Games/UE_5.8', [switch]$SkipBuild)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$projectFile=Join-Path $projectRoot 'Constellation.uproject'
$logDir=Join-Path $projectRoot 'Saved/Logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
if(-not $SkipBuild) {
    & (Join-Path $EngineRoot 'Engine/Build/BatchFiles/Build.bat') ConstellationEditor Win64 Development "-Project=$projectFile" -WaitMutex -NoHotReloadFromIDE *> (Join-Path $logDir 'SceneDirector-build.log')
    if($LASTEXITCODE -ne 0) { throw "Build failed. See $logDir/SceneDirector-build.log" }
}
$log=Join-Path $logDir 'SceneDirector-tests.log'
& (Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe') $projectFile /Engine/Maps/Entry -unattended -nop4 -nosplash -NullRHI '-ExecCmds=Automation RunTests Constellation.SceneDirector' '-TestExit=Automation Test Queue Empty' "-abslog=$log" *> (Join-Path $logDir 'SceneDirector-tests-console.log')
$processResult=$LASTEXITCODE
$lines=Get-Content -LiteralPath $log
$completed=@($lines | Select-String 'Test Completed. Result=')
$failed=@($lines | Select-String 'Result=\{Fail\}|LogAutomationController: Error:|Fatal error:')
$completed | ForEach-Object { $_.Line }
if($processResult -ne 0 -or $failed.Count -gt 0 -or $completed.Count -lt 25) { throw "Tests failed or incomplete. See $log" }
Write-Output "Scene Director: $($completed.Count) tests passed."

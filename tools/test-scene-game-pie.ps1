param([string]$EngineRoot='C:/Program Files/Epic Games/UE_5.8')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$run=Join-Path $root ('Saved/SceneReleaseValidation/PIE-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $run -Force | Out-Null
$log=Join-Path $run 'pie.log'
& (Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe') (Join-Path $root 'Constellation.uproject') -unattended -nullrhi -nosplash -NoSound "-UserDir=$run" "-ExecCmds=py $root/tools/verify-scene-game-pie.py" "-abslog=$log" *> (Join-Path $run 'console.log')
$exit=$LASTEXITCODE
$report=Join-Path $run 'Saved/scene-pie-result.json'
if($exit -ne 0 -or !(Test-Path -LiteralPath $report)) { throw "PIE process failed ($exit); see $log" }
$result=Get-Content -LiteralPath $report -Raw | ConvertFrom-Json
$errors=@(Select-String -LiteralPath $log -Pattern 'Mobility of .*has to be .Movable.|Ensure condition failed:|Fatal error:|LogBlueprint: Error:|LogScript: Error:|LogPython: Error:')
if(!$result.success -or $errors.Count) { throw "PIE validation failed: $($result.error). Engine errors: $($errors.Count). See $log" }
Write-Output "Actual-map PIE validation passed. Report: $report"

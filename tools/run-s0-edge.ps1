param([ValidateSet('art1','final')][string]$Stage='art1',[switch]$CorrectEdge)
$projectRoot=Split-Path $PSScriptRoot -Parent
$outRoot=Join-Path $projectRoot 'Saved/S0WetFloor/EdgePass_20261017'
$scriptName=if($Stage -eq 'final'){'review-s0-edge.py'}else{'edge-s0-classroom.py'}
$mode='-ExecCmds="py '+$projectRoot+'/tools/'+$scriptName+'" -Polish'+$Stage+' -RenderOffscreen -windowed -ResX=1600 -ResY=900'
$argLine='"'+$projectRoot+'/Constellation.uproject" '+$mode+' -NoAssetRegistryCache -NoAssetRegistryCacheWrite -unattended -nosplash -nop4 -UserDir="'+$outRoot+'/User" -abslog="'+$outRoot+'/'+$Stage+'.log"'
if($Stage -in @('art1')){$argLine+=' -PolishHold'}
if($CorrectEdge){$argLine+=' -CorrectEdge'}
$job=Start-Process 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe' -ArgumentList $argLine -WindowStyle Hidden -PassThru
Write-Output ($Stage+': PID '+$job.Id)

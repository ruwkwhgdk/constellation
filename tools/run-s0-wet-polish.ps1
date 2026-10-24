param([ValidateSet('test1','test2','test3','film1','final')][string]$Stage='test1')
$projectRoot=Split-Path $PSScriptRoot -Parent
$outRoot=Join-Path $projectRoot 'Saved/S0WetFloor/Polish_20261017'
$scriptName=if($Stage -eq 'final'){'review-s0-wet-polish.py'}else{'polish-s0-wet-floor.py'}
$mode='-ExecCmds="py '+$projectRoot+'/tools/'+$scriptName+'" -Polish'+$Stage+' -RenderOffscreen -windowed -ResX=1600 -ResY=900'
$argLine='"'+$projectRoot+'/Constellation.uproject" '+$mode+' -NoAssetRegistryCache -NoAssetRegistryCacheWrite -unattended -nosplash -nop4 -UserDir="'+$outRoot+'/User" -abslog="'+$outRoot+'/'+$Stage+'.log"'
if($Stage -in @('test2','film1')){$argLine+=' -PolishHold'}
$job=Start-Process 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe' -ArgumentList $argLine -WindowStyle Hidden -PassThru
Write-Output ($Stage+': PID '+$job.Id)

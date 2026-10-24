param([string]$Suffix='2022',[string]$RunName='TestProject01')
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
if($RunName -notmatch '^TestProject[0-9]+$'){throw 'Invalid test folder'}
$testRoot=Join-Path $projectRoot "Saved/PhoneMenu/$RunName"
if(Test-Path -LiteralPath $testRoot){throw 'Use a fresh run folder'}
New-Item -ItemType Directory -Path (Join-Path $testRoot 'Binaries/Win64') -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot 'Constellation.uproject') -Destination $testRoot
Copy-Item -LiteralPath (Join-Path $projectRoot 'Config') -Destination $testRoot -Recurse
foreach($folder in @('Content','Plugins')){
 New-Item -ItemType Junction -Path (Join-Path $testRoot $folder) -Target (Join-Path $projectRoot $folder) | Out-Null
}
Copy-Item -LiteralPath (Join-Path $projectRoot "Binaries/Win64/UnrealEditor-Constellation-$Suffix.dll") -Destination (Join-Path $testRoot 'Binaries/Win64/UnrealEditor-Constellation.dll')
$manifest=Get-Content -LiteralPath (Join-Path $projectRoot 'Binaries/Win64/UnrealEditor.modules') -Raw | ConvertFrom-Json
$manifest.Modules.Constellation='UnrealEditor-Constellation.dll'
$manifest | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $testRoot 'Binaries/Win64/UnrealEditor.modules') -Encoding utf8
# This process reads existing Content/Plugins. No script saves or imports assets.
& 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe' (Join-Path $testRoot 'Constellation.uproject') -unattended -nullrhi -nosound -nop4 -NoLiveCoding -NoHotReload -DDC-ForceMemoryCache '-ExecCmds=Automation RunTests Constellation.PhoneMenu' '-TestExit=Automation Test Queue Empty' "-abslog=$testRoot/tests.log" *> (Join-Path $testRoot 'console.log')
exit $LASTEXITCODE

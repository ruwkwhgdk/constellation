param([string]$EngineRoot = 'C:/Program Files/Epic Games/UE_5.8')
$projectRoot = Split-Path $PSScriptRoot -Parent
& (Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe') (Join-Path $projectRoot 'Constellation.uproject') '/Game/Constellation/Review/CombatCore/L_CombatCore' -game -windowed -ResX=1280 -ResY=720

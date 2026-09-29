$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectFile = Join-Path $projectRoot 'Constellation.uproject'
$editorExe = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
if (!(Test-Path -LiteralPath $editorExe)) { throw 'Unreal Editor not found' }
# Explicitly invoked local play helper; never automatically launched by production.
Start-Process -FilePath $editorExe -ArgumentList @(
    ('"' + $projectFile + '"'),
    '/Game/Environment/OvergrownHall/TripoFull/Maps/L_OvergrownHall_TripoFull',
    '-game', '-windowed', '-ResX=1280', '-ResY=720', '-nop4'
) -WindowStyle Normal

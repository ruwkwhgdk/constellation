$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectFile = Join-Path $projectRoot 'Constellation.uproject'
$editorExe = 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
$gameLog = Join-Path $projectRoot 'Saved\Logs\StairwellPlay.log'
if (!(Test-Path -LiteralPath $editorExe)) { throw "Unreal Editor not found: $editorExe" }
# Interactive game window requested by the user; editor sessions are left running.
$gameProcess = Start-Process -FilePath $editorExe -ArgumentList @(
    ('"' + $projectFile + '"'),
    '/Game/Environment/StairwellModular/Scene/Maps/L_Stairwell_PlayScale2',
    '-game', '-windowed', '-ResX=1280', '-ResY=900', '-nop4',
    ('-abslog="' + $gameLog + '"')
) -WindowStyle Normal -PassThru
Write-Output "Stairwell game process: $($gameProcess.Id)"

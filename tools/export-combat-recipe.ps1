param(
    [string]$Id='SlimeScout_v1',
    [string]$NewId='SlimeScout_v2',
    [string]$Baseline='CombatRecipes/SlimeScout_v1.json',
    [string]$EngineRoot='C:/Program Files/Epic Games/UE_5.8'
)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$old=@($env:COMBAT_EXPORT_ID,$env:COMBAT_EXPORT_NEW_ID,$env:COMBAT_EXPORT_BASELINE)
try {
    $env:COMBAT_EXPORT_ID=$Id
    $env:COMBAT_EXPORT_NEW_ID=$NewId
    $env:COMBAT_EXPORT_BASELINE=if($Baseline){(Resolve-Path -LiteralPath $Baseline).Path}else{''}
    $log=Join-Path $projectRoot 'Saved/Logs/Combat-recipe-export.log'
    & (Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe') (Join-Path $projectRoot 'Constellation.uproject') -run=pythonscript "-script=$PSScriptRoot/export-combat-recipe.py" -unattended -nop4 -nosplash -NullRHI "-abslog=$log" *> (Join-Path $projectRoot 'Saved/Logs/Combat-recipe-export-console.log')
    if($LASTEXITCODE -ne 0){throw "Export failed. See $log"}
    Get-Content -LiteralPath (Join-Path $projectRoot 'Saved/CombatAudit/recipe-export-result.json')
} finally {
    $env:COMBAT_EXPORT_ID=$old[0]
    $env:COMBAT_EXPORT_NEW_ID=$old[1]
    $env:COMBAT_EXPORT_BASELINE=$old[2]
}

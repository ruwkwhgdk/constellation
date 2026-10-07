param(
    [string]$Recipe = 'CombatRecipes/SlimeScout_v1.json',
    [switch]$Apply,
    [string]$EngineRoot = 'C:/Program Files/Epic Games/UE_5.8'
)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$recipePath=(Resolve-Path -LiteralPath $Recipe).Path
$oldInput=$env:COMBAT_RECIPE_INPUT
$oldApply=$env:COMBAT_RECIPE_APPLY
$oldResult=$env:COMBAT_RECIPE_RESULT
try {
    $env:COMBAT_RECIPE_INPUT=$recipePath
    $env:COMBAT_RECIPE_APPLY=if($Apply){'1'}else{'0'}
    $mode=if($Apply){'apply'}else{'preview'}
    $jobId=[Guid]::NewGuid().ToString('N')
    $folder=Join-Path $projectRoot "Saved/CombatAudit/RecipeJobs/$jobId"
    New-Item -ItemType Directory -Force $folder | Out-Null
    $env:COMBAT_RECIPE_RESULT=Join-Path $folder 'result.json'
    $log=Join-Path $folder 'engine.log'
    Write-Output "Recipe job: $folder"
    & (Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe') (Join-Path $projectRoot 'Constellation.uproject') -run=pythonscript "-script=$PSScriptRoot/import-combat-recipe.py" -unattended -nop4 -nosplash -NullRHI "-abslog=$log" *> (Join-Path $folder "console.log")
    if($LASTEXITCODE -ne 0){throw "Recipe $mode failed. See $log"}
    if(!(Test-Path -LiteralPath $env:COMBAT_RECIPE_RESULT)){throw "Recipe result missing. See $log"}
    $result=Get-Content -LiteralPath $env:COMBAT_RECIPE_RESULT -Raw | ConvertFrom-Json
    if(!$result.passed -or $result.mode -ne $mode){throw "Recipe incomplete: $($result.error). See $log"}
    Get-Content -LiteralPath $env:COMBAT_RECIPE_RESULT
} finally {
    $env:COMBAT_RECIPE_INPUT=$oldInput
    $env:COMBAT_RECIPE_APPLY=$oldApply
    $env:COMBAT_RECIPE_RESULT=$oldResult
}

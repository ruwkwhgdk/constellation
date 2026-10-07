[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Id='CombatTool_v3',
    [string]$EngineRoot='C:/Program Files/Epic Games/UE_5.8',
    [ValidateRange(800,7680)][int]$Width=1600,
    [ValidateRange(600,4320)][int]$Height=900
)
$ErrorActionPreference='Stop'
if($Id -notmatch '^[A-Za-z][A-Za-z0-9_]{0,47}$'){throw 'Invalid recipe id'}
$projectRoot=Split-Path $PSScriptRoot -Parent
$projectFile=Join-Path $projectRoot 'Constellation.uproject'
$engineExe=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
if(-not(Test-Path -LiteralPath $engineExe)){throw "Unreal Engine executable not found: $engineExe"}
if(-not(Test-Path -LiteralPath $projectFile)){throw "Project not found: $projectFile"}
if(-not(Test-Path -LiteralPath (Join-Path $projectRoot "Content/Constellation/Review/CombatRecipes/$Id/L_Preview.umap"))){throw 'Generate this recipe before playing it.'}
# A saved map alone does not prove a version-2 creation completed.
$recipe=Join-Path $projectRoot "CombatRecipes/$Id.json"
$data=Get-Content -LiteralPath $recipe -Raw | ConvertFrom-Json
if($data.schema_version -eq 2){
    $manifestPath=Join-Path $projectRoot "CombatRecipes/$Id.manifest.json"
    $snapshotPath=Join-Path $projectRoot "CombatRecipes/$Id.resolved.json"
    if(!(Test-Path -LiteralPath $manifestPath) -or !(Test-Path -LiteralPath $snapshotPath)){throw 'Creation incomplete: choose a completed version or create a new version.'}
    $manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
    $hash=(Get-FileHash -LiteralPath $snapshotPath -Algorithm SHA256).Hash
    if(!$manifest.complete -or $manifest.id -ne $Id -or $manifest.recipe_sha256 -ne $hash){throw 'Authoring provenance check failed. Choose a verified version.'}
}
$gameArguments=@(
    ('"{0}"' -f $projectFile),
    "/Game/Constellation/Review/CombatRecipes/$Id/L_Preview",
    '-game', '-windowed', '-NoDebugExecBindings', "-ResX=$Width", "-ResY=$Height"
)
if($PSCmdlet.ShouldProcess("$engineExe $($gameArguments -join ' ')",'Launch combat play window')){
    Start-Process -FilePath $engineExe -ArgumentList $gameArguments -WorkingDirectory $projectRoot
}

$ErrorActionPreference='Stop'
$workspace=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$art=[IO.Path]::GetFullPath((Join-Path $workspace 'ArtSource/Stairwell_Modular'))
$workflow=Join-Path $art 'Workflow'
$targets=[Collections.Generic.List[string]]::new()
# Exact audited Unreal packages, never an unchecked directory tree.
$audit=Get-Content (Join-Path $workflow 'asset_cleanup.json') -Raw | ConvertFrom-Json
foreach($package in $audit.candidates){
    if($audit.protected -contains $package){continue}
    if(@($audit.references.$package).Count -ne 0){throw "Unexpected reference: $package"}
    if(!$package.StartsWith('/Game/Environment/StairwellModular/') -and $package -ne '/Game/Blueprints/Character/PC/CameraBackups/BP_Player_Heroine_BeforeStairCamera'){throw 'Unexpected asset scope'}
    $relative=$package.Substring(6)
    foreach($ext in '.umap','.uasset'){
        $f=Join-Path $workspace ('Content/'+$relative+$ext)
        if(Test-Path -LiteralPath $f){$targets.Add($f)}
    }
}
Get-ChildItem -LiteralPath $art -Recurse -File | Where-Object { $_.Extension -eq '.log' -or $_.Extension -eq '.blend1' -or $_.Name -like 'balance_*.json' } | ForEach-Object {$targets.Add($_.FullName)}
$scene=Join-Path $art 'Scene/v001'
Get-ChildItem -LiteralPath $scene -File | Where-Object {
    ($_.Extension -eq '.png' -and $_.Name -ne 'after_finish_revision.png') -or
    ($_.Extension -eq '.html' -and $_.Name -notin @('finish_revision.html','review.html')) -or
    ($_.Extension -eq '.md') -or
    ($_.Name -in @('before_landing_revision.json','camera_geometry_verification.json','details_verification.json','landing_revision_verification.json','lighting_before_details.json','lighting_verification.json','material_verification.json','width240_verification.json','apply_details_report.json','apply_lighting_report.json'))
} | ForEach-Object {$targets.Add($_.FullName)}
foreach($relative in @('Scene/v002/details_pass01.png','Models/15_Light/light15_view_a.png','Models/15_Light/light15_view_b.png','Models/15_Light/tripo_preview_v001.webp')){
    $f=Join-Path $art $relative; if(Test-Path -LiteralPath $f){$targets.Add($f)}
}
$retired=@('capture_stairwell_scene.py','revise_stairwell_camera.py','revise_stairwell_details.py','revise_stairwell_finish.py','revise_stairwell_lighting.py','revise_stairwell_materials.py','save_stairwell_camera_backup.py','finalize_stairwell_scale2.py','validate_stairwell_details.py','verify_stair_camera_saved.py','inspect_heroine_camera.py','check_stairwell_play.py')
foreach($name in $retired){$f=Join-Path $workspace ('Content/Python/'+$name); if(Test-Path -LiteralPath $f){$targets.Add($f)}}
$records=@()
foreach($target in ($targets | Sort-Object -Unique)){
    $full=[IO.Path]::GetFullPath($target)
    if(!$full.StartsWith($workspace+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw "Outside workspace: $full"}
    $item=Get-Item -LiteralPath $full
    if($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)){throw "Unexpected directory/link: $full"}
    $records+=@{path=$full.Substring($workspace.Length+1);bytes=$item.Length}
}
$report=@{deleted_files=$records;count=$records.Count;bytes=($records|Measure-Object -Property bytes -Sum).Sum;status='planned'}
[IO.File]::WriteAllText((Join-Path $workflow 'file_cleanup.json'),($report|ConvertTo-Json -Depth 8))
foreach($r in $records){Remove-Item -LiteralPath (Join-Path $workspace $r.path)}
foreach($r in $records){if(Test-Path -LiteralPath (Join-Path $workspace $r.path)){throw "Deletion failed: $($r.path)"}}
$report.status='deleted_and_verified'; [IO.File]::WriteAllText((Join-Path $workflow 'file_cleanup.json'),($report|ConvertTo-Json -Depth 8))
$audit.deleted=@($audit.candidates | Where-Object {$audit.protected -notcontains $_}); $audit.failed=@(); $audit | Add-Member -NotePropertyName deletion_method -NotePropertyValue 'Reference-checked Unreal delete API attempted; remaining exact package files removed after engine exit and verified on disk' -Force
[IO.File]::WriteAllText((Join-Path $workflow 'asset_cleanup.json'),($audit|ConvertTo-Json -Depth 15))
Write-Output "Removed $($report.count) files; $([math]::Round($report.bytes/1MB,2)) MiB"

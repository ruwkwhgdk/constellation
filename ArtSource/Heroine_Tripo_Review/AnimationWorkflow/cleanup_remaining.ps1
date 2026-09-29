$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\User\Documents\UnrealProjects\Constellation'
$sourceRoot = Join-Path $taskRoot 'ArtSource\Heroine_Tripo_Review'
$retired = Join-Path $sourceRoot 'RunPolish'
$kept = Join-Path $sourceRoot 'RunSoft'
# User requested obsolete animation polishing artifacts removed. Preserve and
# verify the actual mesh reimport source, texture payload, weights and backups.
foreach ($name in @('SK_player_heroine_new_RunPreview.fbx','garment_weights.json')) {
 if ((Get-FileHash -LiteralPath (Join-Path $retired $name)).Hash -ne (Get-FileHash -LiteralPath (Join-Path $kept $name)).Hash) { throw "Copy mismatch: $name" }
}
$textures = Join-Path $retired 'SK_player_heroine_new_RunPreview.fbm'
foreach ($file in Get-ChildItem -LiteralPath $textures -File -Recurse) {
 $relative = $file.FullName.Substring($retired.Length+1)
 if ((Get-FileHash -LiteralPath $file.FullName).Hash -ne (Get-FileHash -LiteralPath (Join-Path $kept $relative)).Hash) { throw "Texture mismatch: $relative" }
}
foreach ($name in @('ReferenceMotion\Reference_Run.fbx','ReferenceMotion\reference_motion.json','ReferenceMotion\source_rest_canonical.json','ConnectionBackups\userpref_before_mcp.blend','ConnectionBackups\blender_mcp_protocol5_backup.py')) {
 if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot $name))) { throw "Missing preserved file: $name" }
}
$record = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'unreal_cleanup_result.json') -Raw | ConvertFrom-Json
if ([IO.Path]::GetFullPath($record.mesh_source) -ne (Join-Path $kept 'SK_player_heroine_new_RunPreview.fbx')) { throw 'Reimport path not updated' }
$allEntries = @(Get-ChildItem -LiteralPath $retired -Recurse -Force)
if ($allEntries | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }) { throw 'Reparse point encountered' }
$files = @($allEntries | Where-Object { -not $_.PSIsContainer })
$records = @()
foreach ($file in $files) {
 $absolute = [IO.Path]::GetFullPath($file.FullName)
 if (-not $absolute.StartsWith($retired+'\',[StringComparison]::OrdinalIgnoreCase)) { throw 'Outside RunPolish' }
 $records += [pscustomobject]@{path=$absolute;bytes=$file.Length}
}
# Fixed map filenames, previously audited: no referencers outside the retired set.
$previewRoot = Join-Path $taskRoot 'Content\Resources\Characters\PC\player_heroine_new\Preview'
foreach ($name in @('L_player_heroine_new_Run_Natural.umap','L_player_heroine_new_Run_Polish.umap')) {
 $absolute=[IO.Path]::GetFullPath((Join-Path $previewRoot $name))
 if ([IO.Path]::GetDirectoryName($absolute) -ne $previewRoot) { throw 'Outside preview directory' }
 if (Test-Path -LiteralPath $absolute) {
  $file=Get-Item -LiteralPath $absolute
  $records += [pscustomobject]@{path=$absolute;bytes=$file.Length}
 }
}
$records | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $PSScriptRoot 'remaining_cleanup_manifest.json') -Encoding UTF8
foreach ($entry in $records) { Remove-Item -LiteralPath $entry.path -Force }
foreach ($directory in ($allEntries | Where-Object PSIsContainer | Sort-Object { $_.FullName.Length } -Descending)) { Remove-Item -LiteralPath $directory.FullName }
Remove-Item -LiteralPath $retired
$records | Measure-Object bytes -Sum | Select-Object Count,Sum

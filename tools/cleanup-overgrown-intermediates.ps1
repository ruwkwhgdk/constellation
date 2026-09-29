$ErrorActionPreference='Stop'
$projectRoot=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$hallRoot=[IO.Path]::GetFullPath((Join-Path $projectRoot 'ArtSource/OvergrownHall'))
$targets=@(Get-ChildItem -LiteralPath $hallRoot -Recurse -File | Where-Object { $_.Extension -in '.log','.blend1','.pyc' -or $_.Name -match '^SM_OH_Rounded.*\.(blend|fbx)$' })
foreach($relative in @('TripoReplacement/v006/probe_mirror.png','TripoReplacement/v006/probe_water.png','TripoReplacement/v012/probe.png')) {
    $candidate=Join-Path $hallRoot $relative
    if(Test-Path -LiteralPath $candidate){$targets+=Get-Item -LiteralPath $candidate}
}
$records=@()
foreach($item in ($targets|Sort-Object FullName -Unique)) {
    $full=[IO.Path]::GetFullPath($item.FullName)
    if(!$full.StartsWith($hallRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw "Outside hall: $full"}
    $records+=[pscustomobject]@{path=$full.Substring($projectRoot.Length+1).Replace('\','/');bytes=$item.Length;sha256=(Get-FileHash -LiteralPath $full -Algorithm SHA256).Hash}
    Remove-Item -LiteralPath $full -Force
}
$report=Join-Path $hallRoot 'Workflow/file_cleanup.json'
# Preserve the first cleanup evidence when this idempotent helper is run again.
if($records.Count -gt 0 -or !(Test-Path -LiteralPath $report)){$records|ConvertTo-Json -Depth 4|Set-Content -LiteralPath $report -Encoding utf8}
Write-Output ('Removed {0} files, {1:N2} MB' -f $records.Count,(($records|Measure-Object bytes -Sum).Sum/1MB))

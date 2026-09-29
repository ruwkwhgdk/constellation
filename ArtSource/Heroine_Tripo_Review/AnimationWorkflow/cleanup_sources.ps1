$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$projectRoot = [IO.Path]::GetFullPath((Join-Path $taskRoot '../..'))
if ($taskRoot -ne (Join-Path $projectRoot 'ArtSource/Heroine_Tripo_Review')) { throw 'Unexpected source root' }
$candidates = @('RunNatural','RunRetarget','RunSoft/soften.py','RunSoft/prepare_tools.py')
# The Polish mesh source is retained until Unreal import metadata has been updated.
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'unreal_cleanup_result.json')) { $candidates += 'RunPolish' }
$records = @()
foreach ($relative in $candidates) {
    $target = [IO.Path]::GetFullPath((Join-Path $taskRoot $relative))
    if (-not $target.StartsWith($taskRoot + [IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw "Outside source root: $target" }
    if (-not (Test-Path -LiteralPath $target)) { continue }
    $entry = Get-Item -LiteralPath $target
    if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point: $target" }
    $files = if ($entry.PSIsContainer) { @(Get-ChildItem -LiteralPath $target -File -Recurse) } else { @($entry) }
    if ($entry.PSIsContainer -and (Get-ChildItem -LiteralPath $target -Recurse | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })) { throw "Nested reparse point: $target" }
    foreach ($file in $files) { $records += [pscustomobject]@{path=$file.FullName;bytes=$file.Length} }
    Remove-Item -LiteralPath $target -Recurse -Force
    if (Test-Path -LiteralPath $target) { throw "Deletion incomplete: $target" }
}
$manifest = Join-Path $PSScriptRoot 'source_cleanup_manifest.json'
$prior = if (Test-Path -LiteralPath $manifest) { @(Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json) } else { @() }
@($prior + $records) | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath $manifest -Encoding UTF8
$records | Measure-Object -Property bytes -Sum | Select-Object Count,Sum

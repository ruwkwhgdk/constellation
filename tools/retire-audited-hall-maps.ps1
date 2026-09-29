$ErrorActionPreference='Stop'
$projectRoot=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$auditPath=Join-Path $projectRoot 'ArtSource/OvergrownHall/Workflow/asset_cleanup.json'
$audit=Get-Content -LiteralPath $auditPath -Raw|ConvertFrom-Json
# Exact four failed Unreal-API deletions; never broaden this list from the audit.
$packages=@(
 '/Game/Environment/OvergrownHall/Blockout/Maps/L_OvergrownHall_Blockout',
 '/Game/Environment/OvergrownHall/Production/Maps/L_OvergrownHall_Detail',
 '/Game/Environment/OvergrownHall/Scene/Maps/L_OvergrownHall_Layout',
 '/Game/Environment/OvergrownHall/TripoReplacement/Maps/L_OvergrownHall_TripoReview'
)
$contentRoot=[IO.Path]::GetFullPath((Join-Path $projectRoot 'Content/Environment/OvergrownHall'))
$backupRoot=Join-Path $projectRoot 'Saved/EnvironmentCleanupRecovery'
New-Item -ItemType Directory -Path $backupRoot -Force|Out-Null
$plan=@()
# Complete every validation and reversible backup before the first deletion.
foreach($package in $packages){
 if($audit.candidates -notcontains $package -or $audit.protected -contains $package){throw 'Not an audited obsolete map'}
 foreach($ref in $audit.references.$package){
  if($ref -ne $package){
   $refFile=Join-Path $projectRoot ('Content/'+$ref.Substring(6)+'.uasset')
   if(Test-Path -LiteralPath $refFile){throw "Referencer still exists: $ref"}
  }
 }
 $file=[IO.Path]::GetFullPath((Join-Path $projectRoot ('Content/'+$package.Substring(6)+'.umap')))
 if(!$file.StartsWith($contentRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Outside permitted root'}
 if(!(Test-Path -LiteralPath $file)){throw 'Expected map missing; review rather than guessing'}
 $backup=Join-Path $backupRoot ([IO.Path]::GetFileName($file))
 $sha=(Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash
 Copy-Item -LiteralPath $file -Destination $backup -Force
 if((Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash -ne $sha){throw 'Backup hash mismatch'}
 $plan+=[pscustomobject]@{package=$package;file=$file;backup=$backup;sha256=$sha}
}
$plan|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $backupRoot 'manifest.json') -Encoding utf8
foreach($entry in $plan){Remove-Item -LiteralPath $entry.file -Force}
$deleted=@()
foreach($p in $audit.candidates){
 if($audit.protected -contains $p){continue}
 if((Test-Path -LiteralPath (Join-Path $projectRoot ('Content/'+$p.Substring(6)+'.uasset'))) -or (Test-Path -LiteralPath (Join-Path $projectRoot ('Content/'+$p.Substring(6)+'.umap')))){throw 'Unexpected package remains'}
 $deleted+=$p
}
$audit.deleted=$deleted;$audit.failed=@()
$audit|Add-Member -NotePropertyName map_file_fallback -NotePropertyValue $plan -Force
$audit|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $auditPath -Encoding utf8
Write-Output "Confirmed $($deleted.Count) obsolete packages removed; four map backups in ignored Saved/EnvironmentCleanupRecovery."

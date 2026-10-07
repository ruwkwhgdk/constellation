param(
 [string]$Id='CombatTool_v1',
 [int]$Width=1600,
 [int]$Height=900,
 [int]$FPS=60,
 [switch]$Group
)
$ErrorActionPreference='Stop'
. "$PSScriptRoot/combat-process.ps1"
if($Id -notmatch '^[A-Za-z][A-Za-z0-9_]{0,47}$'){throw 'Invalid recipe id'}
$root=Split-Path $PSScriptRoot -Parent
$out=Join-Path $root "Saved/CombatAudit/$(if($Group){'Group'}else{'Special'})/$($Width)x$($Height)-$FPS"
New-Item -ItemType Directory -Force $out | Out-Null
$log=Join-Path $out 'game.log'
$args=@(('"{0}"' -f (Join-Path $root 'Constellation.uproject')),"/Game/Constellation/Review/CombatRecipes/$Id/L_Preview",
 '-game','-windowed','-RenderOffscreen','-ForceRes','-NoDebugExecBindings',"-ResX=$Width","-ResY=$Height",'-unattended','-nop4','-nosplash',$(if($Group){'-CombatGroupReview'}else{'-CombatSpecialReview'}),('"-ExecCmds=t.MaxFPS {0}"' -f $FPS),('"-abslog={0}"' -f $log))
$p=Start-Process -FilePath 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe' -ArgumentList $args -WindowStyle Hidden -PassThru
try{$exitCode=Wait-CombatProcess -Process $p -TimeoutSeconds 180}finally{$p.Dispose()}
$text=Get-Content -LiteralPath $log -Raw
if($exitCode -ne 0 -or $text -notmatch $(if($Group){'COMBAT_GROUP_REVIEW PASS'}else{'COMBAT_SPECIAL_REVIEW PASS'}) -or $text -match 'Combat(Special|Group).*Review: FAIL|Fatal error:|Assertion failed:'){throw "Special review failed. See $log"}
if(!$Group){Copy-Item -LiteralPath (Join-Path $root 'Saved/CombatAudit/Special/loadout.png') -Destination (Join-Path $out 'loadout.png') -Force}
Write-Output "PASS: $(if($Group){'Group AI, completion and restart'}else{'Q/E gameplay'}) at $Width x $Height / $FPS FPS"

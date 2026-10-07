param([string]$Id='CombatTool_v3',[switch]$Slots)
$ErrorActionPreference='Stop'
. "$PSScriptRoot/combat-process.ps1"
if($Id -notmatch '^[A-Za-z][A-Za-z0-9_]{0,47}$'){throw 'Invalid recipe id'}
$root=Split-Path $PSScriptRoot -Parent
$mode=if($Slots){'slots'}else{'combat'}
$log=Join-Path $root "Saved/Logs/Combat-VFX-$mode-play.log"
$args=@(('"{0}"' -f (Join-Path $root 'Constellation.uproject')),"/Game/Constellation/Review/CombatRecipes/$Id/L_Preview",'-game','-windowed','-RenderOffscreen','-ForceRes','-ResX=1600','-ResY=900','-NoDebugExecBindings','-unattended','-nop4','-nosplash',('-'+$(if($Slots){'CombatVFXSlotReview'}else{'CombatVFXReview'})),('"-abslog={0}"' -f $log))
$p=Start-Process 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe' -ArgumentList $args -WindowStyle Hidden -PassThru
try{$code=Wait-CombatProcess -Process $p -TimeoutSeconds 180}finally{$p.Dispose()}
$text=Get-Content -LiteralPath $log -Raw
$marker=if($Slots){'COMBAT_VFX_SLOT_REVIEW PASS'}else{'COMBAT_VFX_REVIEW \{"passed":true'}
if($code -ne 0 -or $text -notmatch $marker -or $text -match 'CombatVFXSlot.*: FAIL|Fatal error:'){throw "VFX play check failed: $log"}
Write-Output "PASS: $mode VFX in $Id"

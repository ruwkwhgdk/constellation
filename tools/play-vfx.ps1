param([ValidateSet('Gallery','Glass','Benchmark','Probe')][string]$Mode='Gallery',[switch]$Capture)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path $PSScriptRoot -Parent
$editor=Join-Path ${env:ProgramFiles} 'Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe'
if(!(Test-Path -LiteralPath $editor)){throw "Unreal Engine 5.8 editor not found: $editor"}
$map='L_VFXGallery'
$launchArgs=@(('"'+(Join-Path $projectRoot 'Constellation.uproject')+'"'),('/Game/Constellation/Review/VFX/'+$map),'-game','-windowed','-ResX=1280','-ResY=720','-nosplash')
if($Mode -eq 'Probe'){$launchArgs+='-VFXGalleryProbe'}
elseif($Mode -eq 'Glass'){$launchArgs+='-VFXGlassReview'}
elseif($Mode -eq 'Benchmark'){$launchArgs+='-VFXBenchmark'}
elseif($Capture){$launchArgs+='-VFXGalleryCapture'}
if($Capture){$launchArgs+=@('-RenderOffscreen','-unattended','-nosound','-NoScreenMessages')}
$launchArgs+=('-abslog="'+(Join-Path $projectRoot ('Saved/Logs/VFX-'+$Mode.ToLower()+'-render.log'))+'"')
# A visible window is intentional only when the user explicitly runs this preview launcher.
if($Capture){$p=Start-Process $editor -ArgumentList $launchArgs -WindowStyle Hidden -PassThru}else{$p=Start-Process $editor -ArgumentList $launchArgs -PassThru}
Write-Output "VFX $Mode process $($p.Id)"
if($Capture){$p.WaitForExit();exit $p.ExitCode}

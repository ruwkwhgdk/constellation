param(
    [string]$Id='SlimeScout_v2',
    [ValidateRange(30,600)][int]$TimeoutSeconds=180,
    [ValidateRange(5,120)][int]$ScenarioSeconds=18,
    [string]$EngineRoot='C:/Program Files/Epic Games/UE_5.8'
)
$ErrorActionPreference='Stop'
. "$PSScriptRoot/combat-play-result.ps1"
. "$PSScriptRoot/combat-process.ps1"
if($Id -notmatch '^[A-Za-z][A-Za-z0-9_]{0,47}$'){throw 'Invalid recipe id'}
$projectRoot=Split-Path $PSScriptRoot -Parent
$map="/Game/Constellation/Review/CombatRecipes/$Id/L_Preview"
if(-not(Test-Path -LiteralPath (Join-Path $projectRoot "Content/Constellation/Review/CombatRecipes/$Id/L_Preview.umap"))){throw 'Generate this recipe before testing it.'}
$engine=Join-Path $EngineRoot 'Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
if(-not(Test-Path -LiteralPath $engine)){throw "Missing engine: $engine"}
$runId=[Guid]::NewGuid().ToString('N')
$runDir=Join-Path $projectRoot "Saved/CombatAudit/PlayRuns/$runId"
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
$log=Join-Path $runDir 'game.log'
$report=[ordered]@{passed=$false;run_id=$runId;recipe_id=$Id;map=$map;started_utc=[DateTime]::UtcNow.ToString('o');scenario='Obstacle approach with profile-based exit/return/recovery';scenario_seconds=$ScenarioSeconds;failure='';checks=$null;log=$log}
$process=$null
try {
    $arguments=@(
        ('"{0}"' -f (Join-Path $projectRoot 'Constellation.uproject')),
        $map,'-game','-RenderOffscreen','-windowed','-ResX=1280','-ResY=720',
        '-unattended','-nop4','-nosplash','-CombatEncounterReview',"-CombatReviewSeconds=$ScenarioSeconds",('"-abslog={0}"' -f $log)
    )
    $process=Start-Process -FilePath $engine -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runDir 'console.log') -RedirectStandardError (Join-Path $runDir 'stderr.log')
    $exitCode=Wait-CombatProcess -Process $process -TimeoutSeconds $TimeoutSeconds
    $contents=if(Test-Path -LiteralPath $log){Get-Content -LiteralPath $log -Raw}else{''}
    $parsed=Read-CombatPlayResult -LogText $contents -ExitCode $exitCode -ExpectedSchemaVersion 2
    $report.passed=$parsed.passed; $report.failure=$parsed.failure; $report.checks=$parsed.checks
} catch {
    $report.failure=$_.Exception.Message
} finally {
    if($process){$process.Dispose()}
    $report['finished_utc']=[DateTime]::UtcNow.ToString('o')
    $reportPath=Join-Path $runDir 'result.json'
    $report | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $reportPath -Encoding utf8
}
if(-not $report.passed){throw "$($report.failure). Report: $reportPath"}
Write-Output "PASS: $Id standard encounter playback"
Write-Output "Report: $reportPath"

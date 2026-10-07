$ErrorActionPreference='Stop'
. "$PSScriptRoot/combat-play-result.ps1"
$good='COMBAT_ENCOUNTER_REVIEW {"passed":true,"chased":true,"attacked":true,"returned_and_restored":true,"return_cancelled_action":true,"detour_y":268.9}'
$profiled='COMBAT_ENCOUNTER_REVIEW {"schema_version":2,"passed":true,"scenario_valid":true,"chased":true,"attacked":true,"returned":true,"recovery_policy_matched":true,"return_cancelled_action":true,"detour_y":269}'
$cases=@(
    @{Log=$profiled;Code=0;Pass=$true},
    @{Log=$profiled.Replace('"recovery_policy_matched":true','"recovery_policy_matched":false');Code=0;Pass=$false},
    @{Log=$profiled.Replace('"scenario_valid":true','"scenario_valid":false');Code=0;Pass=$false},
    @{Log=$profiled.Replace('"schema_version":2','"schema_version":999');Code=0;Pass=$false},
    @{Log=$good;Code=0;Pass=$true},
    @{Log='';Code=0;Pass=$false},
    @{Log='COMBAT_ENCOUNTER_REVIEW null';Code=0;Pass=$false},
    @{Log=($good+[Environment]::NewLine+'Fatal error: shutdown failure');Code=0;Pass=$false},
    @{Log=$good;Code=1;Pass=$false},
    @{Log=$good.Replace('"attacked":true','"attacked":false');Code=0;Pass=$false},
    @{Log=$good.Replace('"passed":true','"passed":"true"');Code=0;Pass=$false},
    @{Log=$good.Replace('268.9','12');Code=0;Pass=$false},
    @{Log=($good+[Environment]::NewLine+$good);Code=0;Pass=$false},
    @{Log='COMBAT_ENCOUNTER_REVIEW invalid json';Code=0;Pass=$false}
)
foreach($case in $cases) {
    $result=Read-CombatPlayResult -LogText $case.Log -ExitCode $case.Code
    if($result.passed -ne $case.Pass){throw "Unexpected result: $($case.Log)"}
    if(-not $result.passed -and -not $result.failure){throw 'Missing actionable failure'}
}
$legacy=Read-CombatPlayResult -LogText $good -ExitCode 0 -ExpectedSchemaVersion 2
if($legacy.passed -or -not $legacy.failure){throw 'Current runner accepted stale runtime schema'}
Write-Output "PASS: $($cases.Count + 1) playback result checks"

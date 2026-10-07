function Read-CombatPlayResult {
    param([string]$LogText,[int]$ExitCode,[int]$ExpectedSchemaVersion=0)
    $result=[ordered]@{passed=$false;failure='';checks=$null}
    if($ExitCode -ne 0){$result.failure="Game process exited with code $ExitCode";return $result}
    $matches_=[regex]::Matches($LogText,'(?m)COMBAT_ENCOUNTER_REVIEW ([^\r\n]+)')
    if($matches_.Count -ne 1){$result.failure="Expected one result from this run; found $($matches_.Count)";return $result}
    try {$data=$matches_[0].Groups[1].Value | ConvertFrom-Json -ErrorAction Stop}
    catch {$result.failure='Game result is not valid JSON';return $result}
    if($data -isnot [PSCustomObject]){$result.failure="Game result must be a JSON object";return $result}
    if($LogText -match "Fatal error:|Assertion failed:"){$result.failure="Fatal runtime error in this run";return $result}
    $result.checks=$data
    $versionProperty=$data.PSObject.Properties['schema_version']
    $version=if($versionProperty){$versionProperty.Value}else{1}
    if($version -isnot [int] -and $version -isnot [long]){$result.failure='Invalid result schema version';return $result}
    if($version -notin @(1,2) -or ($ExpectedSchemaVersion -ne 0 -and $version -ne $ExpectedSchemaVersion)){
        $result.failure="Unsupported result schema $version; rebuild the editor for the current runner";return $result
    }
    $required=if($version -eq 2){@('passed','scenario_valid','chased','attacked','returned','recovery_policy_matched','return_cancelled_action')}else{@('passed','chased','attacked','returned_and_restored','return_cancelled_action')}
    $failed=@()
    foreach($key in $required) {
        $property=$data.PSObject.Properties[$key]
        if(-not $property -or $property.Value -isnot [bool] -or $property.Value -ne $true){$failed+=$key}
    }
    $detour=$data.PSObject.Properties['detour_y']
    if(-not $detour -or $detour.Value -is [bool] -or $detour.Value -is [string] -or
       $detour.Value -isnot [ValueType] -or [double]::IsNaN([double]$detour.Value) -or
       [double]::IsInfinity([double]$detour.Value) -or [double]$detour.Value -le 200){$failed+='obstacle_detour'}
    if($failed.Count){$result.failure='Scenario checks incomplete: '+($failed -join ', ');return $result}
    $result.passed=$true
    return $result
}

param()
$ErrorActionPreference='Stop'
. "$PSScriptRoot/combat-process.ps1"
$dir=Join-Path (Split-Path $PSScriptRoot -Parent) ("Saved/CombatAudit/ProcessRunnerTests/"+[Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $dir -Force | Out-Null
foreach($expected in @(0,7)) {
    $p=Start-Process -FilePath "$env:SystemRoot/System32/cmd.exe" -ArgumentList "/c exit $expected" -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $dir "$expected.log")
    try {
        $actual=Wait-CombatProcess -Process $p -TimeoutSeconds 10
        if($null -eq $actual -or $actual -ne $expected){throw "Expected exit $expected; got [$actual]"}
    } finally {$p.Dispose()}
}
$p=Start-Process -FilePath "$env:SystemRoot/System32/WindowsPowerShell/v1.0/powershell.exe" -ArgumentList '-NoProfile -Command "Start-Sleep -Seconds 20"' -PassThru -WindowStyle Hidden
try {
    $timedOut=$false
    try {Wait-CombatProcess -Process $p -TimeoutSeconds 1 | Out-Null}
    catch {if($_.Exception.Message -notlike '*timeout*'){throw};$timedOut=$true}
    if(-not $timedOut -or -not $p.HasExited){throw 'Timed out test process was not stopped'}
} finally {if(-not $p.HasExited){$p.Kill()};$p.Dispose()}
Write-Output "PASS: 3 process checks on PowerShell $($PSVersionTable.PSVersion)"

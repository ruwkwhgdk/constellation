function Wait-CombatProcess {
    param(
        [Parameter(Mandatory=$true)][System.Diagnostics.Process]$Process,
        [ValidateRange(1,3600)][int]$TimeoutSeconds
    )
    # Windows PowerShell 5.1 can lose ExitCode after a redirected process exits.
    # Retain the process handle before waiting; never infer success from a null code.
    $null=$Process.Handle
    if(-not $Process.WaitForExit($TimeoutSeconds*1000)) {
        $Process.Kill()
        $null=$Process.WaitForExit(5000)
        throw "Process timeout after $TimeoutSeconds seconds; only this test process was stopped."
    }
    $Process.WaitForExit()
    $Process.Refresh()
    $code=$Process.ExitCode
    if($null -eq $code){throw 'Process exited but its exit code is unavailable.'}
    return [int]$code
}

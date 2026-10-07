$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$python=Join-Path $env:LOCALAPPDATA 'Programs/Python/Python312/pythonw.exe'
if(-not(Test-Path -LiteralPath $python)){
    $command=Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if(-not $command){throw 'Python 3 is required to open the combat authoring tool.'}
    $python=$command.Source
}
Start-Process -FilePath $python -ArgumentList ('"{0}"' -f (Join-Path $PSScriptRoot 'combat_author_launch.py')) -WorkingDirectory $root -WindowStyle Hidden

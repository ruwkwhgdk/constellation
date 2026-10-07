@echo off
setlocal
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\play-combat-recipe.ps1" %*
if errorlevel 1 (
    echo.
    echo Combat launch failed. See the message above.
    pause
    exit /b 1
)
exit /b 0

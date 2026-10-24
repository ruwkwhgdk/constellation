@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if not exist Saved\PhoneMenu mkdir Saved\PhoneMenu
cl /nologo /std:c++17 /EHsc /W4 Tests\PhoneMenuStateTests.cpp /FoSaved\PhoneMenu\PhoneMenuStateTests.obj /FeSaved\PhoneMenu\PhoneMenuStateTests.exe
if errorlevel 1 exit /b 1
Saved\PhoneMenu\PhoneMenuStateTests.exe

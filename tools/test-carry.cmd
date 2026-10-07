@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if not exist Saved\CarryTests mkdir Saved\CarryTests
cl /nologo /std:c++17 /EHsc /W4 Tests\CarryMathTests.cpp /FoSaved\CarryTests\CarryMathTests.obj /FeSaved\CarryTests\CarryMathTests.exe
if errorlevel 1 exit /b 1
Saved\CarryTests\CarryMathTests.exe

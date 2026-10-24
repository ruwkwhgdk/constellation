@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if not exist Saved\FallSystem mkdir Saved\FallSystem
cl /nologo /std:c++17 /EHsc /W4 Tests\FallMathTests.cpp /FoSaved\FallSystem\FallMathTests.obj /FeSaved\FallSystem\FallMathTests.exe
if errorlevel 1 exit /b 1
Saved\FallSystem\FallMathTests.exe

@echo off
call "C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat" >nul
if not exist Saved\SubwayTests mkdir Saved\SubwayTests
cl /nologo /EHsc /W4 Tests\SubwayTravelGateTests.cpp /FoSaved\SubwayTests\TravelTests.obj /FeSaved\SubwayTests\TravelTests.exe
if errorlevel 1 exit /b 1
Saved\SubwayTests\TravelTests.exe

@echo off
echo Building WWM.exe...
cd /d %~dp0
pyinstaller build.spec
echo Done! Check dist\WWM.exe
pause

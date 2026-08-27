@echo off
echo Building w-execute.exe...
cd /d %~dp0
pyinstaller --clean --noconfirm build.spec
echo Done! Check dist\w-execute.exe
pause

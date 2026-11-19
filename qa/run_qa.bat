@echo off
rem Runs every Kinship check. Double-click it, or run: qaun_qa.bat --quick   (add --live to also check the live site)
cd /d "%~dp0.."
python qaun_all.py %*
echo.
pause

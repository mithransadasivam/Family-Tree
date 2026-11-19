@echo off
rem Groot: runs every Kinship website check. Double-click it, or run: groot\groot.bat --quick   (add --live to also check the live site)
cd /d "%~dp0.."
python grootun_all.py %*
echo.
pause

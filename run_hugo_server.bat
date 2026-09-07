@echo off
cd /d "%~dp0"
start "Hugo Server" cmd /k "hugo server"
timeout /t 3 /nobreak >nul
start "" http://localhost:1313

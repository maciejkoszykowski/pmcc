@echo off
cd /d "%~dp0"
start "Hugo Server" cmd /k "hugo server -D"
timeout /t 3 /nobreak >nul
start "" http://localhost:1313

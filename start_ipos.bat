@echo off
title IPOS Fiscal Tracker Server

:: ወደ ፕሮጀክቱ ፎልደር መግባት
cd /d "%~dp0"

:: FastAPI ሰርቨሩን ከጀርባ (Minimized) ማስነሳት
start /min "IPOS_API" cmd /c "python -m uvicorn main:app --host 0.0.0.0 --port 8000"

:: ሰርቨሩ እስኪነሳ 3 ሰከንድ መጠበቅ
timeout /t 3 /nobreak > nul

:: Google Chrome ላይ ገጹን በራሱ መክፈት
start chrome "http://127.0.0.1:8000"
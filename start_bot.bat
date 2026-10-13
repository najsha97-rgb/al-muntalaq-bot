@echo off
chcp 65001 > nul
title BOT TELEGRAM AL-MUNTALAQ
echo ===================================================================
echo             MEMULAKAN BOT TELEGRAM AL-MUNTALAQ                    
echo ===================================================================
echo.
cd /d "%~dp0"
"C:\Users\pc\AppData\Local\Python\pythoncore-3.14-64\python.exe" bot.py
echo.
pause

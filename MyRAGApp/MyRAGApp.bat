@echo off
setlocal

cd /d "%~dp0"

echo Starting MyRAGApp...
echo.

runtime\python.exe app\main.py

if errorlevel 1 (
    echo.
    echo MyRAGApp failed to start.
    echo Please see the error above.
    pause
)

endlocal
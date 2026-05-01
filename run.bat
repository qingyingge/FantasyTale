@echo off
cd /d "%~dp0"
echo ============================================
echo   Fantasy Tale - Game Launcher
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    pause
    exit /b 1
)

python -c "import pygame" >nul 2>&1
if errorlevel 1 (
    echo Installing pygame...
    pip install pygame
)

python -c "import numpy" >nul 2>&1
if errorlevel 1 (
    echo Installing numpy...
    pip install numpy
)

echo.
echo Starting game...
start "" pythonw game.py
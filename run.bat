@echo off
setlocal EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ============================================
echo   RPG Game Launcher
echo ============================================
echo.

set "PYTHON="
set "FULL_VENV=%SCRIPT_DIR%venv\Scripts\python.exe"

REM 检查venv
if exist "%FULL_VENV%" (
    echo [OK] Using venv
    set "PYTHON=%FULL_VENV%"
    goto :check_deps
)

REM 检查py launcher版本
py -3.11 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Using Python 3.11
    set "PYTHON=py -3.11"
    goto :check_deps
)

py -3.12 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Using Python 3.12
    set "PYTHON=py -3.12"
    goto :check_deps
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Using system Python
    set "PYTHON=py"
    goto :check_deps
)

REM 未找到Python，询问是否下载
echo.
echo [!] Python not found
echo.
echo Options:
echo   1. Download Python 3.11 (recommended)
echo   2. Exit
echo.

set /p CHOICE="Choose (1-2): "
if "%CHOICE%"=="1" (
    echo.
    echo Downloading Python 3.11...
    echo This may take a few minutes...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile '%TEMP%\python-installer.exe'"
    echo Starting installer...
    echo.
    echo IMPORTANT: Check "Add Python to PATH" and click Install!
    start "" "%TEMP%\python-installer.exe"
    echo.
    echo After installation, run this launcher again.
    pause
    exit /b 1
) else (
    exit /b 1
)

:check_deps
echo.

REM 检查并安装依赖
%PYTHON% -m pip show pygame >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Installing pygame...
    %PYTHON% -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pygame --timeout 100
)

%PYTHON% -m pip show numpy >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Installing numpy...
    %PYTHON% -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple numpy --timeout 100
)

echo.
echo Starting game...
echo ----------------------------------------

%PYTHON% game.py

echo.
echo ----------------------------------------
echo Game exited
pause
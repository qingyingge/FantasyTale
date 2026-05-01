@echo off

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo ============================================
echo   RPG Game Launcher
echo ============================================
echo.

set "PYTHON="
set "FULL_VENV=%SCRIPT_DIR%venv\Scripts\pythonw.exe"

if exist "%FULL_VENV%" (
    echo [OK] Using venv
    set "PYTHON=%FULL_VENV%"
    goto :check_deps
)

set "FULL_VENV=%SCRIPT_DIR%venv\Scripts\python.exe"

if exist "%FULL_VENV%" (
    echo [OK] Using venv
    set "PYTHON=%FULL_VENV%"
    goto :check_deps
)

py -3.11 --version >nul 2>&1
if errorlevel 0 (
    echo [OK] Using Python 3.11
    for /f "delims=" %%i in ('py -3.11 -c "import sys; print(sys.executable)"') do set "SYSTEM_PYTHON=%%i"
    set "PYTHONW=%SYSTEM_PYTHON:~0,-10%pythonw.exe"
    if exist "%PYTHONW%" (
        set "PYTHON=%PYTHONW%"
    ) else (
        set "PYTHON=py -3.11"
    )
    goto :check_deps
)

py -3.12 --version >nul 2>&1
if errorlevel 0 (
    echo [OK] Using Python 3.12
    for /f "delims=" %%i in ('py -3.12 -c "import sys; print(sys.executable)"') do set "SYSTEM_PYTHON=%%i"
    set "PYTHONW=%SYSTEM_PYTHON:~0,-10%pythonw.exe"
    if exist "%PYTHONW%" (
        set "PYTHON=%PYTHONW%"
    ) else (
        set "PYTHON=py -3.12"
    )
    goto :check_deps
)

py --version >nul 2>&1
if errorlevel 0 (
    echo [OK] Using system Python
    for /f "delims=" %%i in ('py -c "import sys; print(sys.executable)"') do set "SYSTEM_PYTHON=%%i"
    set "PYTHONW=%SYSTEM_PYTHON:~0,-10%pythonw.exe"
    if exist "%PYTHONW%" (
        set "PYTHON=%PYTHONW%"
    ) else (
        set "PYTHON=py"
    )
    goto :check_deps
)

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

%PYTHON% -m pip show pygame >nul 2>&1
if errorlevel 1 (
    echo [!] Installing pygame...
    %PYTHON% -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pygame --timeout 100
)

%PYTHON% -m pip show numpy >nul 2>&1
if errorlevel 1 (
    echo [!] Installing numpy...
    %PYTHON% -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple numpy --timeout 100
)

echo.
echo Starting game...
echo ----------------------------------------

start "" "%PYTHON%" game.py
exit

echo.
echo ----------------------------------------
echo Game exited
pause
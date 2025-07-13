@echo off
echo Deploying PDF Translator...

REM Remove existing virtual environment
if exist venv rmdir /s /q venv

REM Create new virtual environment
python -m venv venv
if errorlevel 1 (
    echo Failed to create virtual environment
    exit /b 1
)

REM Upgrade pip
venv\Scripts\python -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip
    exit /b 1
)

REM Install dependencies
venv\Scripts\pip install --no-cache-dir -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies
    exit /b 1
)

echo.
echo ✓ Deployment completed successfully!
echo Your PDF Translator is ready to use!
echo.
echo To activate the environment, run: venv\Scripts\activate
pause
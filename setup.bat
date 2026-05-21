@echo off
echo ========================================
echo  PT. Remenia Satori Tepas
echo ========================================
echo.

REM Check Python version
python --version
if errorlevel 1 (
    echo Error: Python not found!
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install individual packages (to avoid conflicts)
echo Installing packages...
pip install numpy==1.26.4
pip install pandas==2.2.1
pip install streamlit==1.29.0
pip install plotly==5.18.0
pip install scikit-learn==1.4.0
pip install openpyxl==3.1.2
pip install python-dateutil==2.8.2

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo To run: run.bat
pause
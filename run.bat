@echo off
echo ========================================
echo  PT. Remenia Satori Tepas
echo ========================================
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run Streamlit app
echo Starting application...
echo.
echo 🌐 Open browser: http://localhost:8501
echo ⏸️  Press Ctrl+C to stop
echo.
streamlit run app.py --server.port 8501
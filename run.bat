@echo off
:: Activate the Python environment
Call ".venv\Scripts\activate.bat"

:: Change to the app directory
:: cd /d "%~dp0app"

:: Start Python and run the Dash app
start "Dash Server" python app\app.py

:: Go back to the original directory
:: cd /d "%~dp0"

:: Wait for the server to start
timeout /t 8

:: Open the default web browser and navigate to the Dash app
start http://127.0.0.1:8050/

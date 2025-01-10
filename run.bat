@echo off
:: Activate the Python environment
Call "venv\Scripts\activate.bat"

:: Start Python and run the Dash app
start "Dash Server" python app.py

timeout /t 5

:: Open the default web browser and navigate to the Dash app
start http://127.0.0.1:8050/

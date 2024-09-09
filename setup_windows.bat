@echo off

python -m venv .venv
call .venv\Scripts\activate.bat

pip install -e .

pip install -r requirements.txt

echo Setup complete..

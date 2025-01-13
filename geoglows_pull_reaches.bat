@echo off
REM ============================================================
REM Script to update the HorizonsRC/geoglows-scheduled-task repo
REM activate a Python virtual environment,
REM and run the geoglows_pull_reaches.py script
REM ============================================================

REM Path to the .env file
set ENV_FILE=C:\Scripts\geoglows_pull_reaches\.env

REM Load environmen variables from .env file
REM Each line in .env file should be in the format: KEY=VALUE
REM See .env.example for an example .env file
for /f "tokens=1,2 delims== " %%A in ('type %ENV_FILE%') do (
    set VAR=%%B
    set VAR=%VAR:"=%
    set %%A=%VAR%
)

REM Navigate to the git repository
cd %REPO_PATH%

echo Pulling the latest changes from git...
git pull origin main

echo Activating the virtual environment...
call %REPO_PATH%\venv\Scripts\activate

echo Installing the required packages...
pip install --no-cache-dir -r requirements.txt

echo Running the Python script...
python geoglows_pull_reaches.py

echo Deactivating the virtual environment...
deactivate

echo Done.

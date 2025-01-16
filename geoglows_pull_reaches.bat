@echo off
REM ============================================================
REM Script to update the HorizonsRC/geoglows-scheduled-task repo
REM activate a Python virtual environment,
REM and run the geoglows_pull_reaches.py script
REM ============================================================

REM Path to the .env file
REM Assuming that the .env file is in the same directory as this script
set ENV_FILE=.env

REM Load environmen variables from .env file
REM Each line in .env file should be in the format: KEY=VALUE
REM See .env.example for an example .env file
echo Loading environment variables from %ENV_FILE%...
FOR /F "delims== tokens=1,* eol=#" %%i in (%ENV_FILE%) do SET %%i=%%~j

echo REPO_PATH=%REPO_PATH%
echo REACH_FILE=%REACH_FILE%
echo OUTPUT_FILE=%OUTPUT_FILE%
echo BACKUP_DIR=%BACKUP_DIR%
echo LOG_DIR=%LOG_DIR%

REM Navigate to the git repository
cd %REPO_PATH%

echo Pulling the latest changes from git...
git pull origin main

echo Activating the virtual environment...
call %REPO_PATH%\venv\Scripts\activate

echo Installing the required packages...
pip install --no-cache-dir -r requirements.txt

echo Running the Python script...
REM Piping the output to find "ERROR" to check for errors... somehow
python geoglows_pull_reaches.py | find "ERROR" >nul2>nul

if ERRORLEVEL 1 (
  echo Error running the Python script. Searching for the temp file...
  REM The temp file has the same filename, but with a .temp extension
  set OUTPUT_FILE_TEMP=%OUTPUT_FILE:.csv=.temp%
  echo Looking for temp file: %OUTPUT_FILE_TEMP%
  REM REM If the temp file exists, rename it to the output file using xcopy
  if exist "%OUTPUT_FILE_TEMP%" (
    echo Renaming the temp file to the output file...
    xcopy "%OUTPUT_FILE_TEMP%" "%OUTPUT_FILE%" /Y /R
    REM Delete the temp file
    del "%OUTPUT_FILE_TEMP%"
  )
)

echo Deactivating the virtual environment...
deactivate

echo Done.

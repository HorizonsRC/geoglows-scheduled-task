# geoglows-scheduled-task
A simple script to pull data from the GeoGlows python API library and save to a network folder. 

In production on PNT-AP41, scheduled to run every day at midnight.

## System Requirements

* Git

* Python > 3.8

## Steps to get this running on a production server

1. Pull the repo to `C:\Scripts`. If this location is not viable the `.bat` script would need to be updated.

2. Create a file named `.env` in the repo. Optionally make a copy of `.env.example` and rename it to `.env`.

3. Substitute the example paths in your `.env` file, using `.env.example` as an example.

4. Create a python virtual environment in the repo directory. This can be done by running the following command in the command prompt:
```bash
cd C:\Scripts\geoglows-scheduled-task
python -m venv venv
```
The `.gitignore` file is set to ignore the `venv` folder. The `.bat` script will activate the virtual environment before running the script.

5. Run the `.bat` script to install the required packages and run the python script. This can be done by running the following command in the command prompt:
```bash
geoglows-scheduled-task.bat
```
The `.bat` script will update the git repo, activate the virtual environment, install the required packages, and run the python script.

6. The `.bat` script can be scheduled to run at a specific time using the Windows Task Scheduler.

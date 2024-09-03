@echo off
:: Prompt the user to input the callsign
set /p CALLSIGN="Enter the callsign: "

:: Change the directory to C:/QSL
cd /d C:/QSL

:: Execute the Python script with the user-provided callsign
python fetch_qrz_data.py --callsign %CALLSIGN% --update

:: Pause the script to keep the window open after execution
pause

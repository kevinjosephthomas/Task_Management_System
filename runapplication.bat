@echo off
echo Starting backend...
REM "start" opens the backend in its own window so the script can continue to the frontend.
start "Backend" cmd /k "call env\Scripts\activate && python main.py"
echo Starting frontend...
cd frontend
call npm start

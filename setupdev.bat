@echo off
echo Setting up backend...
python -m venv env
call env\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
python scripts\seed.py
echo Setting up frontend...
cd frontend
call npm install
cd ..
echo Setup complete.

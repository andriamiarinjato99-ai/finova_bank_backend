@echo off
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env copy .env.example .env
python manage.py makemigrations
python manage.py migrate
python manage.py seed_demo
echo.
echo Backend pret.
echo Swagger: http://127.0.0.1:8000/api/docs/
echo Admin:   http://127.0.0.1:8000/admin/
echo.
python manage.py runserver

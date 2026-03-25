# first time setup venv
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate

# enter venv
source .venv/bin/activate
pip install -r requirements.txt
# Update the .env file based on your local setup.
cp .env.example .env 

# Open .env if setup superbase, if keep local development， go to migrate& run backend

# To use PostgreSQL (e.g. Supabase):
USE_SQLITE=False
# Then configure:
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

# migrate& run backend
python manage.py migrate
python manage.py runserver

# Run (local)
cd backend
source .venv/bin/activate
python manage.py runserver


# Access
# Backend server:
http://127.0.0.1:8000/
# Admin panel:
http://127.0.0.1:8000/admin/

# Admin Account(Create an admin user:)
python manage.py createsuperuser




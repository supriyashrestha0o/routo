# Route Backend

Student-focused ride-sharing and journey-matching API built with Django and Django REST Framework.

## Team Members

- Armita Thapa Magar (@armitathapa-hub)
- Shreya Maharjan (@shreyamaharjan018-ship-it)
- Supriya Shrestha (@supriyashrestha0o)

## Local setup

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py runserver
```

Configure `.env` before starting the server. `DJANGO_DEBUG=false` requires a strong `DJANGO_SECRET_KEY`, a Firebase service-account path, and complete Cloudinary credentials. The project uses MySQL 8 by default; set `DB_ENGINE=sqlite` only for lightweight local development.

Run the test suite with:

```powershell
python manage.py test
```

See `API.md` for endpoint contracts and request examples.

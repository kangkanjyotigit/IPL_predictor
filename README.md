# DreamKaroCricket

Cricket match and Dream11 fantasy-team prediction system. Built as three cooperating
parts that grew into one product.

## What's here

| Folder | What it is |
|---|---|
| `dreamkaro/`, `matches/`, `users/` | **Django REST backend** — match and player models, DRF serializers, REST views, Celery tasks, a management command that seeds sample data |
| `Dockerfile`, `docker-compose.yml`, `nginx.conf`, `letsencrypt-docker-compose.yml` | Production deployment: Django + PostgreSQL + Redis/Celery behind nginx with TLS |
| `flask-app/` | **Flask front end** — API routes, form handling, server-rendered templates, and a test suite |
| `dreamteam-tools/` | Supporting toolbelt: LLM API wrapper, web scraper, search engine helper, screenshot utilities |

## Stack

Python · Django · Django REST Framework · Celery · PostgreSQL · Redis · Flask ·
SQLAlchemy · Docker · nginx · pandas · scikit-learn

## Running the Django backend

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py create_sample_data
python manage.py runserver
```

## Running the Flask app

```bash
cd flask-app
pip install -r requirements.txt
python run.py
```

## Notes

- Large raw datasets (ball-by-ball IPL deliveries, 2008-2024) are not committed.
  Point the import scripts at your own Cricsheet CSV export.
- API keys are read from environment variables. See `flask-app/.env.example`.
- `DJANGO_SECRET_KEY` must be set in production.

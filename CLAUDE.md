# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Takdhum is a Django-based online education platform (Bangladeshi market, Dhaka timezone) for hosting courses, events, and community content.

## Common Commands

```bash
# Run development server
python manage.py runserver

# Database migrations
python manage.py makemigrations
python manage.py migrate

# Create admin superuser
python manage.py createsuperuser

# Collect static files (production)
python manage.py collectstatic

# Run tests
python manage.py test web
```

## Architecture

### Single-app Django structure
- `takdhum/` — project settings, root URL conf, WSGI entry point
- `web/` — the sole Django app containing all models, views, forms, URLs, and templates

### Data model layers
- **User** — Django's built-in `User` + `Profile` model (auto-created via signal), extended with social links, contact info, and profile picture
- **Courses** — `CourseCategory` → `Course` → `SingleVideo` (each video has a public/private flag)
- **Content** — `Event` (with up to 12 gallery images), `Project`, `Testimonial`, `Slider`, `FAQ`
- **Config** — `Basic_info` singleton holds org-wide settings (name, social links, promo video); `AboutUs` for about page content
- **Interactions** — `UserMessage` (contact form), `Subcribe` (email list)

### URL routing
Root conf (`takdhum/urls.py`) delegates everything to `web/urls.py`. Admin is mounted at `/tdlogin/` (not the default `/admin/`). Password reset flows live under `/accounts/` via Django's built-in auth URLs.

### Templates
All templates are under `web/templates/takdhum/` and inherit from `base.html`. Partials (`head.html`, `header.html`, `footer.html`, `script.html`, `meta.html`) are included by the base. Registration/password-reset templates live in `web/templates/registration/`.

### Authentication flow
Registration triggers an email verification step. Token generation is in `web/tokens.py`. The activation email template is `web/templates/acc_active_email.html`.

## Key Settings

- **Database**: SQLite (`db.sqlite3`) for development; MySQL config is commented out in `settings.py` for production use
- **Static files**: served from `static/` in development; `static_cdn/` for production CDN
- **Media files**: uploaded to `media_cdn/`
- **Email**: Gmail SMTP (`smtp.gmail.com:587`) configured in `settings.py`
- **Timezone**: `Asia/Dhaka`
- **Bootstrap version**: 4 (applied via `django-crispy-forms` with `CRISPY_TEMPLATE_PACK = 'bootstrap4'`)
- **Filtering/search**: `django-filter` used in course search views

## Dependencies

```
Django==2.0.3
django-crispy-forms==1.7.2
django-filter==1.1.0
Pillow==5.0.0
pytz==2018.3
```

Install with: `pip install -r requirements.txt`

## Known Issues

- `ALLoWED_HOSTS` is misspelled in `settings.py` (capital `L`) — `ALLOWED_HOSTS` is never actually set, so it defaults to `[]`
- `DEBUG = True` is currently hardcoded; switch to `False` and set `ALLOWED_HOSTS` before any production deployment
- `SECRET_KEY` and `EMAIL_HOST_PASSWORD` are hardcoded in `settings.py` — move to environment variables before deploying
- `web/tests.py` is empty; there is no automated test coverage

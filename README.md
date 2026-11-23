# Student Management - Django backend

REST-style JSON API for the student management site. Students register, submit an
application with a photo, and chat with teachers. Teachers review applications,
approve or reject them, and reply to messages.

Needs **Python 3.10+**. The only dependencies are Django and Pillow (for photo uploads).

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python manage.py makemigrations students
python manage.py migrate
python manage.py seed_demo         # optional: demo teacher + student
python manage.py runserver         # http://127.0.0.1:8000
```

`seed_demo` creates `teacher / teacher123` and `student / student123`. Use it for
development only.

### Creating real teacher accounts

A user is a teacher when `is_staff` is true. Create one with:

```bash
python manage.py createsuperuser
```

Or open `http://127.0.0.1:8000/admin/` and tick **Staff status** on any user.
Students sign up themselves from the website and never get `is_staff`.

## Configuration (environment variables)

| Variable | Default | Purpose |
| --- | --- | --- |
| `DJANGO_DEBUG` | `1` | Set to `0` in production |
| `DJANGO_SECRET_KEY` | dev key | **Required** when `DJANGO_DEBUG` is not `1` |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173,http://127.0.0.1:5173` | Where the React site is served from |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | empty | Only needed for the `/admin/` site behind HTTPS |

Edit the course list in `students/models.py` (`COURSES`). Photo size limit
is `PHOTO_MAX_BYTES` in `sms_backend/settings.py` (2 MB).

## API

All endpoints are under `/api/`. Send `Authorization: Bearer <token>` on protected ones.
Tokens come from login/register and last 7 days.

| Method | Path | Who | What |
| --- | --- | --- | --- |
| POST | `/auth/register/` | public | `{username, email, password}` -> `{token, user}` |
| POST | `/auth/login/` | public | `{username, password}` -> `{token, user}` (`user.role` is `student` or `teacher`) |
| GET | `/auth/me/` | logged in | current user |
| GET | `/courses/` | public | list of courses |
| GET | `/applications/mine/` | student | own application or `null` |
| POST | `/applications/mine/` | student | create/update own application (`multipart/form-data`, field `photo`); editing allowed only while pending |
| GET, POST | `/applications/<id>/messages/` | owner student or teacher | read / send messages `{body}` |
| GET | `/teacher/applications/?status=&q=` | teacher | list + counts, filter by status, search |
| GET, PATCH, DELETE | `/teacher/applications/<id>/` | teacher | view, set `{status, teacher_remarks}`, delete |

Uploaded photos are stored in `media/photos/` and served at `/media/...` while `DEBUG=1`.

## Going to production

- Set `DJANGO_DEBUG=0`, a long random `DJANGO_SECRET_KEY`, real `DJANGO_ALLOWED_HOSTS`, and `CORS_ALLOWED_ORIGINS` to your site's `https://` address.
- Serve behind HTTPS with gunicorn/uvicorn and nginx; have nginx serve `/media/` from `MEDIA_ROOT`.
- Switch `DATABASES` to PostgreSQL and back up the database and `media/` folder.
- Delete the demo accounts and change any passwords created by `seed_demo`.
- Student photos are personal data, and many are of minors. Restrict who can access the server and the `media/` folder, and follow your institution's privacy rules.

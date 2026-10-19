# Event Management System

This is a learning project: an organizer can publish events, and attendees can reserve a place. It uses Python, Flask, SQLite, HTML, and CSS.

## Start the app on Windows

Open Command Prompt in the project folder and run these commands:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open <http://127.0.0.1:5000>. The `Procfile` and `gunicorn` dependency provide the production start command for a hosting service.

Demo organizer sign-in: `organizer` / `event123`.

## What it can do

- Show upcoming events and event details
- Let an organizer create, edit, and delete events
- Let attendees register, while checking capacity and duplicate emails
- Show an organizer the attendee list

## Where to look in the code

- `app.py` contains the Flask routes and database queries.
- `templates/` contains the HTML pages.
- `static/style.css` contains the page styling.
- `instance/events.db` is created automatically when the app starts.

Read [LEARNING_GUIDE.md](LEARNING_GUIDE.md) before using the project in an interview. It walks through the database relationship and the code path for registration, and lists the current limitations honestly.

## Demo-only note

The organizer account and secret key have local development defaults. This setup is for learning on your own computer, not for deploying publicly.

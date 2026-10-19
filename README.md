# Event Management System

A full-stack event management application built with **Python, Flask, SQLite, HTML, and CSS**. Organizers can publish events and manage attendee lists; visitors can browse events and reserve a place.

## Features

- Browse upcoming events and view event details
- Organizer sign-in and event dashboard
- Create, edit, and delete events
- Register attendees and prevent duplicate registrations
- Enforce event capacity during registration
- View the guest list for each event

## Technology

| Layer | Technology |
| --- | --- |
| Server | Python 3, Flask |
| Database | SQLite |
| User interface | HTML templates, CSS |
| Production server | Gunicorn |

## Run locally on Windows

Open Command Prompt in the project folder and run:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open <http://127.0.0.1:5000> in a browser. The SQLite database is created automatically at `instance/events.db`.

**Demo organizer account:** `organizer` / `event123`

## Deploying to Render

When creating a Python web service, use these settings:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`

Configure a private `SECRET_KEY` and organizer credentials in the service's environment variables before deployment.

## How the app works

Flask routes receive browser requests, validate form data, query SQLite, and render templates. Events and registrations are stored in separate tables:

```text
events (id, title, description, location, event_date, capacity)
  └── registrations (id, event_id, attendee_name, attendee_email)
```

One event can have many registrations. Each registration references its event through `event_id`. A database uniqueness constraint prevents the same email from registering for the same event twice. The registration route checks capacity and inserts the registration in a write transaction.

## Project structure

```text
app.py                 Flask routes, validation, and database access
templates/             HTML pages rendered by Flask
static/style.css       Page styles
requirements.txt       Python dependencies
LEARNING_GUIDE.md      Walkthrough of the data model and registration flow
```

## Current scope and next steps

This is a learning and portfolio project. It currently uses one demo organizer account; attendees do not need accounts. Email confirmations and payment processing are not included. The local SQLite database is excluded from the Git repository.

Use persistent storage for the database, or move it to a hosted database, because local SQLite files may not persist on a hosting service. Further improvements could include automated tests, CSRF protection, and support for multiple organizer accounts.

For an interview walkthrough, see [LEARNING_GUIDE.md](LEARNING_GUIDE.md).

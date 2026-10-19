"""A small event management app built with Flask and SQLite."""

import os
import sqlite3
import threading
import webbrowser
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "instance" / "events.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "local-development-key-change-me")
app.config["ORGANIZER_USERNAME"] = os.environ.get("ORGANIZER_USERNAME", "organizer")
app.config["ORGANIZER_PASSWORD_HASH"] = os.environ.get(
    "ORGANIZER_PASSWORD_HASH",
    generate_password_hash(os.environ.get("ORGANIZER_PASSWORD", "event123")),
)


def get_db():
    """Return this request's database connection, creating it when needed."""
    if "db" not in g:
        DATABASE.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def initialize_database():
    db = get_db()
    db.executescript(
        """
        -- An event is saved once, even when many people register for it.
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            event_date TEXT NOT NULL,
            capacity INTEGER NOT NULL CHECK (capacity > 0),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        -- Each registration points back to its event. The pair of event_id
        -- and attendee_email makes duplicate sign-ups for one event impossible.
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
            attendee_name TEXT NOT NULL,
            attendee_email TEXT NOT NULL,
            registered_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(event_id, attendee_email)
        );
        """
    )
    db.commit()
    # A fresh hosted demo should have an event to show on its public home page.
    # Existing databases are left as they are.
    if db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0:
        sample_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%dT%H:%M")
        db.execute(
            """INSERT INTO events
               (title, description, location, event_date, capacity)
               VALUES (?, ?, ?, ?, ?)""",
            (
                "Sample Event: Community Tech Meetup",
                "A sample listing to demonstrate event discovery and attendee registration.",
                "Community Hall",
                sample_date,
                40,
            ),
        )
        db.commit()


@app.before_request
def ensure_database():
    initialize_database()


def organizer_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("organizer_logged_in"):
            flash("Please sign in to open the organizer dashboard.", "info")
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def event_with_registration_count(event_id):
    return get_db().execute(
        """SELECT events.*, COUNT(registrations.id) AS registration_count
           FROM events LEFT JOIN registrations ON events.id = registrations.event_id
           WHERE events.id = ? GROUP BY events.id""",
        (event_id,),
    ).fetchone()


@app.route("/")
def index():
    events = get_db().execute(
        """SELECT events.*, COUNT(registrations.id) AS registration_count
           FROM events LEFT JOIN registrations ON events.id = registrations.event_id
           WHERE events.event_date >= ?
           GROUP BY events.id ORDER BY events.event_date""",
        (datetime.now().strftime("%Y-%m-%dT%H:%M"),),
    ).fetchall()
    return render_template("index.html", events=events)


@app.route("/events/<int:event_id>")
def event_detail(event_id):
    event = event_with_registration_count(event_id)
    if event is None:
        flash("That event could not be found.", "error")
        return redirect(url_for("index"))
    return render_template("event_detail.html", event=event)


@app.post("/events/<int:event_id>/register")
def register(event_id):
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    if len(name) < 2 or "@" not in email or len(email) > 254:
        flash("Enter your name and a valid email address.", "error")
        return redirect(url_for("event_detail", event_id=event_id))

    db = get_db()
    try:
        # Serializing the capacity check and insert prevents overbooking.
        db.execute("BEGIN IMMEDIATE")
        event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
        if event is None:
            db.rollback()
            flash("That event could not be found.", "error")
        else:
            count = db.execute(
                "SELECT COUNT(*) FROM registrations WHERE event_id = ?", (event_id,)
            ).fetchone()[0]
            if count >= event["capacity"]:
                db.rollback()
                flash("Sorry, this event is full.", "error")
            else:
                db.execute(
                    "INSERT INTO registrations (event_id, attendee_name, attendee_email) VALUES (?, ?, ?)",
                    (event_id, name, email),
                )
                db.commit()
                flash("You’re registered! We’ll see you there.", "success")
    except sqlite3.IntegrityError:
        db.rollback()
        flash("This email is already registered for the event.", "error")
    return redirect(url_for("event_detail", event_id=event_id))


@app.route("/organizer/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == app.config["ORGANIZER_USERNAME"] and check_password_hash(
            app.config["ORGANIZER_PASSWORD_HASH"], password
        ):
            session.clear()
            session["organizer_logged_in"] = True
            flash("Welcome back.", "success")
            return redirect(url_for("dashboard"))
        flash("The username or password is incorrect.", "error")
    return render_template("login.html")


@app.post("/organizer/logout")
@organizer_required
def logout():
    session.clear()
    flash("You have signed out.", "info")
    return redirect(url_for("index"))


@app.route("/organizer")
@organizer_required
def dashboard():
    events = get_db().execute(
        """SELECT events.*, COUNT(registrations.id) AS registration_count
           FROM events LEFT JOIN registrations ON events.id = registrations.event_id
           GROUP BY events.id ORDER BY events.event_date DESC"""
    ).fetchall()
    total_registrations = sum(event["registration_count"] for event in events)
    return render_template(
        "dashboard.html", events=events, total_registrations=total_registrations
    )


def validate_event_form():
    data = {
        "title": request.form.get("title", "").strip(),
        "description": request.form.get("description", "").strip(),
        "location": request.form.get("location", "").strip(),
        "event_date": request.form.get("event_date", "").strip(),
        "capacity": request.form.get("capacity", "").strip(),
    }
    errors = []
    if not data["title"] or len(data["title"]) > 100:
        errors.append("Title is required and must be 100 characters or fewer.")
    if not data["description"]:
        errors.append("Add a short event description.")
    if not data["location"] or len(data["location"]) > 120:
        errors.append("Location is required and must be 120 characters or fewer.")
    try:
        parsed_date = datetime.strptime(data["event_date"], "%Y-%m-%dT%H:%M")
        if parsed_date <= datetime.now():
            errors.append("Choose a date and time in the future.")
    except ValueError:
        errors.append("Choose a valid event date and time.")
    try:
        data["capacity"] = int(data["capacity"])
        if not 1 <= data["capacity"] <= 100000:
            errors.append("Capacity must be between 1 and 100,000.")
    except ValueError:
        errors.append("Capacity must be a whole number.")
        data["capacity"] = 1
    return data, errors


@app.route("/organizer/events/new", methods=["GET", "POST"])
@organizer_required
def create_event():
    if request.method == "POST":
        data, errors = validate_event_form()
        if not errors:
            db = get_db()
            db.execute(
                "INSERT INTO events (title, description, location, event_date, capacity) VALUES (?, ?, ?, ?, ?)",
                (data["title"], data["description"], data["location"], data["event_date"], data["capacity"]),
            )
            db.commit()
            flash("Your event is now listed.", "success")
            return redirect(url_for("dashboard"))
        for error in errors:
            flash(error, "error")
        return render_template("event_form.html", event=data, page_title="Create an event")
    return render_template("event_form.html", event={}, page_title="Create an event")


@app.route("/organizer/events/<int:event_id>/edit", methods=["GET", "POST"])
@organizer_required
def edit_event(event_id):
    db = get_db()
    event = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if event is None:
        flash("That event could not be found.", "error")
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        data, errors = validate_event_form()
        registered = db.execute(
            "SELECT COUNT(*) FROM registrations WHERE event_id = ?", (event_id,)
        ).fetchone()[0]
        if data["capacity"] < registered:
            errors.append(f"Capacity cannot be less than the {registered} current registrations.")
        if not errors:
            db.execute(
                "UPDATE events SET title = ?, description = ?, location = ?, event_date = ?, capacity = ? WHERE id = ?",
                (data["title"], data["description"], data["location"], data["event_date"], data["capacity"], event_id),
            )
            db.commit()
            flash("Event details updated.", "success")
            return redirect(url_for("dashboard"))
        for error in errors:
            flash(error, "error")
        return render_template("event_form.html", event=data, page_title="Edit event")
    return render_template("event_form.html", event=event, page_title="Edit event")


@app.post("/organizer/events/<int:event_id>/delete")
@organizer_required
def delete_event(event_id):
    db = get_db()
    db.execute("DELETE FROM events WHERE id = ?", (event_id,))
    db.commit()
    flash("Event and its registrations deleted.", "info")
    return redirect(url_for("dashboard"))


@app.route("/organizer/events/<int:event_id>/attendees")
@organizer_required
def attendees(event_id):
    event = get_db().execute(
        "SELECT * FROM events WHERE id = ?", (event_id,)
    ).fetchone()
    if event is None:
        flash("That event could not be found.", "error")
        return redirect(url_for("dashboard"))
    people = get_db().execute(
        "SELECT attendee_name, attendee_email, registered_at FROM registrations WHERE event_id = ? ORDER BY registered_at",
        (event_id,),
    ).fetchall()
    return render_template("attendees.html", event=event, people=people)


if __name__ == "__main__":
    threading.Timer(1.0, lambda: webbrowser.open_new("http://127.0.0.1:5000")).start()
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")

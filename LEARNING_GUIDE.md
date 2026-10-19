# Learn this project before an interview

Don't try to memorize the whole app. Understand one feature at a time and be honest about what you would improve next.

## First idea: the database relationship

The app has two tables:

```text
events
  id (primary key)
  title, description, location, event_date, capacity

registrations
  id (primary key)
  event_id (foreign key -> events.id)
  attendee_name, attendee_email
```

One event can have many registrations. Each registration belongs to one event. We store event details once in `events`, instead of repeating the title and location on every attendee row.

`event_id` is a foreign key: it connects a registration to an event. `UNIQUE(event_id, attendee_email)` means the same email can register once for a particular event. The same person can still register for a different event.

The table definitions are near the top of `app.py`, inside `initialize_database()`.

## Trace one registration through the app

1. The event page in `templates/event_detail.html` shows a form with a name and email.
2. Submitting it sends a POST request to `/events/<event_id>/register`.
3. The `register()` function in `app.py` reads and checks the form fields.
4. It counts existing registrations for that event and compares the count to capacity.
5. If there is space, it inserts one row into `registrations`.
6. The browser returns to the event page, which now shows the updated spots left.

When explaining this, point at those files and follow the request in order. That demonstrates your understanding much better than reciting a prepared pitch.

## A first interview answer—in your own words

Try explaining this without looking at the paragraph:

> I made an event management app with Flask and SQLite. Events and registrations are stored separately. A registration has an `event_id` that refers to its event, so one event can have many attendees. When someone registers, the app checks the event capacity and whether that email is already registered before saving it.

Change the wording so it sounds like you. If an interviewer asks a follow-up, use the code to show how it works.

## Questions to practice

1. Why did you create separate `events` and `registrations` tables?
2. What does the `event_id` foreign key do?
3. How does the app stop duplicate sign-ups?
4. What happens when an event reaches capacity?
5. What would you improve if you had another week?

Good answers should be based on the code you can point to. For question 5, reasonable next steps include automated tests, CSRF protection, real organizer accounts, and deployment settings.

## Be clear about the current scope

- There is one demo organizer account, configured for local use.
- Attendees do not create accounts; their email identifies a registration.
- There are no email confirmations or payment processing.
- This is a local learning app, not a deployed production service.

These are limits of the current version, not things to hide. You can explain what you would build next and why.

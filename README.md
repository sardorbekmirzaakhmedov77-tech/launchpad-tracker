# Launchpad — Scholarship & Internship Tracker

A calm, attractive workspace for your next chapter. Track opportunities,
application deadlines, preparation checklists, notes, stages, and results.
Built with Python, Flask, SQLite, Jinja, and plain CSS.

## Run locally

Requires Python 3.11 or newer. Open a terminal in this project folder.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

On Windows Command Prompt, use `py -m venv .venv` then
`.venv\Scripts\activate.bat` to create and activate the environment.

Open **http://127.0.0.1:5001**. Keep the terminal open; Ctrl+C stops the server.
For subsequent launches, activate the environment and run `python app.py` again.

The first launch creates six **fictional, clearly labeled example opportunities**.
They are not real offers or verified deadlines. Their dates are relative to the
first launch date. Add real opportunities yourself, using organizer information.

## Features

- Summary of active, preparing, submitted, and soon-due applications.
- Search title, organization, and location; filter type and application stage.
- Sort by deadline, newest, or title.
- Deadline planner for open applications, including overdue ones.
- Add and edit opportunity details, links, benefits, and eligibility notes.
- Saved → Preparing → Submitted → Result stages, with result outcomes.
- Checklists with completion tracking and custom tasks.
- Editable notes and reversible archive.
- Persistent SQLite storage; no API keys, paid services, or external assets.
- Responsive layout, standard HTML forms, no handwritten JavaScript.

## Test it yourself

1. Click **Add opportunity**. Enter a title, organization, type, location, and
   today's deadline. Save. The detail page should say **Due today**.
2. Three starter checklist tasks appear. Click a task to complete it. The progress
   count should change from 0/3 to 1/3. Click again to undo.
3. Add `Request academic transcript`. You should now have four checklist tasks.
4. Set the stage to **Preparing** and click **Update stage**. Return to the
   overview and filter for Preparing to find it.
5. Write a note and click **Save notes**. Refresh the page: the note remains.
6. Click **Edit details**, change the funding or title, and save.
7. Set the stage to **Submitted**. It should disappear from the deadline planner,
   which lists only Saved and Preparing applications.
8. Set the stage to **Result** and outcome to **Accepted**. Save to see the result.
9. Archive it. It disappears from active opportunities and appears in Archive.
   Open it and click **Restore opportunity** to bring it back.
10. Restart the application. Your changes remain saved.

## Automated tests

With the environment activated:

```sh
python -m unittest discover -s tests -v
```

Tests use temporary databases, so they do not change your saved opportunities.

## Files

- `app.py`: database setup, form validation, routes, and basic calculations.
- `templates/`: Jinja HTML pages.
- `static/style.css`: all layout and visual styling.
- `tests/test_app.py`: integration tests for the main workflows.
- `LEARNING_GUIDE.md`: how to rebuild this with course skills.

## Data and scope

The database is `instance/launchpad.db`. Stop the server before copying that file
as a backup. To start fresh, rename it to preserve your old data, then restart.
For a new empty database use `TRACKER_DEMO=0 python app.py` on macOS/Linux; on
Windows run `set TRACKER_DEMO=0` before starting Python. Existing data is never
cleared by this setting.

This version is a **local, single-user learning application**, not a public
multi-user service. It does not fetch listings, send reminders, upload documents,
or submit applications. Deadline calculations use your computer's date; verify
exact closing times/time zones with each organizer. Checklist completion and
application stages are independent—you decide when an application is submitted.
The dashboard totals describe all active entries, regardless of list filters.
Due-soon counts include only open applications with deadlines 0–14 days away.

Use `PORT=5051 python app.py` to choose another port on macOS/Linux. A public
hosting version needs authentication or isolated demo sessions, a stable
`SECRET_KEY`, and production hosting configuration.

# Learn to build Launchpad

This project combines skills taught in Angela Yu's Python bootcamp. It is not an
assignment supplied or endorsed by the course. A few additional engineering
techniques are described explicitly below.

## Course skills in action

| Topic | Use in this project |
|---|---|
| Variables, strings, lists and dictionaries | Opportunities, stages, and form values |
| Functions and if/else | Validation, filters, and deadline labels |
| Loops | Creating checklists and rendering cards |
| Dates | Days remaining until a deadline |
| Exceptions | Friendly errors for invalid form inputs |
| Flask | URL routes, form submissions, and redirects |
| HTML/CSS | Cards, responsive layout, and ordinary browser forms |
| Jinja | Template inheritance, loops, and conditional badges |
| SQL and databases | Saving opportunities and their associated checklist tasks |

SQLite is used through Python's built-in `sqlite3`, rather than an ORM. There is
no frontend framework, AI API, scraper, or custom JavaScript to learn first.

## Follow a request

1. The browser submits the Add opportunity form to `/new`.
2. Flask reads `request.form`, a dictionary-like object.
3. `validate()` checks required text, dates, type, and website links.
4. SQL inserts the opportunity and three starter tasks in one transaction.
5. Flask redirects to the detail page.
6. The detail route queries the data and passes it to a Jinja template.
7. The template displays ordinary HTML styled by CSS.

## Build it in eight small stages

1. Make a Python dictionary with title, organization, type, and deadline.
2. Write a function that calculates days left using `datetime.date`.
3. Store opportunities in SQLite and list them in a terminal.
4. Create a Flask page displaying those records with a Jinja loop.
5. Add a form to create and edit records. Validate on the server.
6. Create a second table for checklist tasks linked by opportunity ID.
7. Add stage updates, search/filtering, notes, and reversible archiving.
8. Add CSS, empty states, sample data, and tests.

Do not copy all the styling first. Get one opportunity working from form to
saved database record, then add features one at a time.

## Small extensions beyond beginner exercises

- **Database transactions:** the connection context manager commits on success,
  rolls back on failure, and closes the connection. This avoids partially saved
  opportunities and checklists.
- **Foreign keys:** each task belongs to a real opportunity.
- **CSRF protection:** a random session token is included in each form and checked
  before changes are accepted. It protects forms; it is not a login system.
- **Safe output and links:** Jinja escapes user text. Website links allow only
  HTTP and HTTPS; SQL values use placeholders instead of string concatenation.
- **Application factory:** `create_app()` accepts a database path, making tests
  independent from your real saved data.
- **Automated integration tests:** Flask's test client simulates form submissions
  without opening a browser. The tests demonstrate complete user workflows.

## Exercises after you understand this version

- Add tags and a tag filter.
- Add an export file for all opportunities.
- Display a monthly deadline calendar.
- Add a reminder system and learn background scheduling.
- Add user accounts before making it a public shared service.

For your portfolio, explain what you understand, rebuild pieces yourself, and
identify any AI assistance honestly if asked. The useful achievement is being
able to maintain and extend the project.

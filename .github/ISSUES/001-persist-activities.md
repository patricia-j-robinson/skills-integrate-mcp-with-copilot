Title: Persist activities in a database (replace in-memory store)

Description:
Move the current in-memory `activities` dict to a persistent database (SQLite/Postgres). Add models, migrations, and use an ORM (e.g., SQLModel or SQLAlchemy). Ensure data persists across restarts.

Acceptance criteria:
- Activities are stored in a DB with fields: name, description, schedule, max_participants, participants.
- Existing API endpoints (`/activities`, signup/unregister) read/write to DB.
- Add migration scripts and update README with DB setup instructions.

Labels: enhancement, backend

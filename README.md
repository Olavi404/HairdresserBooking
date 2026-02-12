# Hairdresser Booking — Minimal App

Simple demo booking system using Flask and in-memory storage.

Quick start

1. Create a virtualenv and install deps:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the app:

```bash
python app.py
```

3. Open http://127.0.0.1:5000 in your browser.

Initialize (SQLite)

Before first run you can initialize the SQLite DB manually:

```bash
python migrate.py
```


Notes

- Data is persisted to SQLite (`data.db`) by default and seeded with sample stylists.
- To reset the DB run `python reset_db.py` (or delete `data.db`).

Admin

- Simple admin UI is available at: http://127.0.0.1:5000/admin
- Admin can view and delete bookings.

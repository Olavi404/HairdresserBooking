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

## Deployment

Deploy to **Render.com** in 10 minutes (free tier available):

1. See [RENDER_DEPLOY.md](RENDER_DEPLOY.md) for step-by-step instructions.
2. Custom domain support: Point `hairdresser.it.com` DNS to Render.
3. Auto-redeploy on every GitHub push.

For VPS deployment (Ubuntu/Debian), see [DEPLOYMENT.md](DEPLOYMENT.md).

## Architecture

- **Backend**: Flask 3.0 with SQLite persistence
- **Frontend**: HTML/CSS/vanilla JavaScript (no frameworks)
- **Stylists**: Pre-seeded with Alice, Bob, Carol
- **Bookings**: Created with conflict detection (no double-booking)
- **Admin**: Delete bookings at `/admin`

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Public booking UI |
| GET | `/admin` | Admin panel |
| GET | `/api/stylists` | List stylists |
| GET | `/api/slots?stylist_id=ID` | Available slots for stylist |
| GET | `/api/bookings` | List all bookings (public view) |
| POST | `/api/book` | Create booking |
| GET | `/api/admin/bookings` | Admin: list all bookings |
| DELETE | `/api/admin/bookings/ID` | Admin: delete booking |

## Testing

Run the test suite:

```bash
pytest tests/
```

Tests cover stylists, slot generation, booking creation, and conflict detection.

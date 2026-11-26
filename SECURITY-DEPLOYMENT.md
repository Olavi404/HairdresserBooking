# Security update — review before deployment

Set FLASK_SECRET_KEY to a strong random value, ADMIN_USERNAME and ADMIN_PASSWORD_HASH to a Werkzeug password hash; APP_ENV=production for HTTPS-only session cookies. Generate locally with Python secrets.token_hex(32) and werkzeug.security.generate_password_hash using getpass; never commit credentials. Without settings admin access is disabled. Back up the live SQLite database outside Git before merging. Existing duplicates block startup; resolve manually, never automatically delete bookings. The public endpoints no longer expose names/phones. Historical Git objects may still contain data; review history and rotate any exposed secrets. Deployment requires HTTPS and login rate limiting at the reverse proxy. This PR does not purge Git history or migrate the live database.

## Migration preflight and limits

Run `python migration_preflight.py /path/to/backup.db` before deploying; it is read-only and reports duplicate groups, invalid slot formats, foreign key violations and integrity. The application uses SQLite-backed fixed-window limits (5 login attempts/minute and 15 booking requests/minute per peer IP). Reverse-proxy deployments must configure trusted client-IP handling carefully; without it, clients may share one limit. Do not trust arbitrary forwarded headers. Browser XSS end-to-end tests remain recommended.

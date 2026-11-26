from flask import Flask, render_template, jsonify, request, session, redirect, url_for, abort
from functools import wraps
from werkzeug.security import check_password_hash
import secrets
import hmac
from datetime import datetime, timedelta
import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
# Allow overriding DB path for tests or custom locations
DB_PATH = os.environ.get('HAIR_DB') or os.path.join(BASE_DIR, 'data.db')

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config.update(SECRET_KEY=os.getenv('FLASK_SECRET_KEY'),
                  SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
                  SESSION_COOKIE_SECURE=os.getenv('APP_ENV') == 'production',
                  PERMANENT_SESSION_LIFETIME=timedelta(hours=2))

def admin_enabled():
    return bool(app.secret_key and os.getenv('ADMIN_USERNAME') and os.getenv('ADMIN_PASSWORD_HASH'))

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not admin_enabled() or not session.get('is_admin'):
            if request.path.startswith('/api/'):
                return jsonify(error='Authentication required'), 401
            return redirect(url_for('admin_login'))
        return func(*args, **kwargs)
    return wrapper

def csrf_valid():
    token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token', '')
    expected = session.get('csrf_token', '')
    return bool(expected and hmac.compare_digest(token.encode(), expected.encode()))

@app.after_request
def prevent_admin_cache(response):
    if request.path.startswith(('/admin', '/api/admin/')):
        response.headers['Cache-Control'] = 'no-store'
    return response

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if not admin_enabled():
        return 'Administrator access not configured', 503
    if request.method == 'POST':
        if not csrf_valid():
            abort(403)
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        if hmac.compare_digest(username.encode(), os.environ['ADMIN_USERNAME'].encode()) and check_password_hash(os.environ['ADMIN_PASSWORD_HASH'], password):
            session.clear()
            session['is_admin'] = True
            session['csrf_token'] = secrets.token_urlsafe(32)
            session.permanent = True
            return redirect(url_for('admin_page'))
        return render_template('login.html', csrf_token=session['csrf_token'], error='Invalid credentials'), 401
    session.setdefault('csrf_token', secrets.token_urlsafe(32))
    return render_template('login.html', csrf_token=session['csrf_token'])

@app.post('/admin/logout')
@admin_required
def admin_logout():
    if not csrf_valid():
        abort(403)
    session.clear()
    return redirect(url_for('admin_login'))

@app.get('/admin')
@admin_required
def admin_page():
    return render_template('admin.html', csrf_token=session['csrf_token'])



def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys = ON')
    conn.execute('PRAGMA busy_timeout = 5000')
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS stylists (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY,
            stylist_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            customer_name TEXT NOT NULL,
            customer_phone TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (stylist_id) REFERENCES stylists(id)
        )
    ''')
    # Fail closed rather than delete existing conflicting reservations.
    try:
        cur.execute('CREATE UNIQUE INDEX IF NOT EXISTS uq_booking_stylist_slot ON bookings(stylist_id, date, time)')
    except sqlite3.IntegrityError:
        conn.rollback()
        conn.close()
        raise RuntimeError('Existing duplicate booking slots; back up and resolve before migration') from None
    # seed stylists if empty
    cur.execute('SELECT COUNT(*) as c FROM stylists')
    if cur.fetchone()['c'] == 0:
        cur.executemany('INSERT INTO stylists (name) VALUES (?)', [(n,) for n in ('Alice','Bob','Carol')])
    conn.commit()
    conn.close()


def generate_slots(days=7):
    slots = []
    for d in range(days):
        day = (datetime.now() + timedelta(days=d)).date()
        for hour in range(9, 17):
            slots.append({"date": day.isoformat(), "time": f"{hour:02d}:00"})
    return slots


# Initialize database on app startup (Flask 3.0+ compatible)
with app.app_context():
    init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/stylists')
def get_stylists():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT id, name FROM stylists ORDER BY id')
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/slots')
def get_slots():
    stylist_id = request.args.get('stylist_id', type=int)
    all_slots = generate_slots(7)
    available = []
    conn = get_db_connection()
    cur = conn.cursor()
    for s in all_slots:
        cur.execute('''SELECT COUNT(*) as c FROM bookings WHERE stylist_id=? AND date=? AND time=?''', (stylist_id, s['date'], s['time']))
        if cur.fetchone()['c'] == 0:
            available.append(s)
    conn.close()
    return jsonify(available)


@app.route('/api/bookings')
def get_bookings():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT stylist_id, date, time FROM bookings ORDER BY date, time')
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/bookings')
@admin_required
def admin_get_bookings():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        SELECT b.id, b.stylist_id, s.name as stylist_name, b.date, b.time, b.customer_name, b.customer_phone, b.created_at
        FROM bookings b JOIN stylists s ON b.stylist_id = s.id
        ORDER BY b.date, b.time
    ''')
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/bookings/<int:booking_id>', methods=['DELETE'])
@admin_required
def admin_delete_booking(booking_id):
    if not csrf_valid():
        return jsonify(error='Invalid CSRF token'), 403
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) as c FROM bookings WHERE id=?', (booking_id,))
    if cur.fetchone()['c'] == 0:
        conn.close()
        return jsonify({'error': 'not found'}), 404
    cur.execute('DELETE FROM bookings WHERE id=?', (booking_id,))
    conn.commit()
    conn.close()
    return jsonify({'deleted': booking_id})


@app.route('/api/book', methods=['POST'])
def book():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Invalid JSON'), 400
    stylist = data.get('stylist_id')
    date = data.get('date')
    time = data.get('time')
    name = data.get('customer_name')
    phone = data.get('customer_phone', '')
    if type(stylist) is not int or not all(isinstance(x, str) for x in (date, time, name, phone)) or not name.strip() or len(name) > 120 or len(phone) > 40:
        return jsonify(error='Invalid booking fields'), 400
    if {'date': date, 'time': time} not in generate_slots(7):
        return jsonify(error='Invalid booking slot'), 400
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        if not cur.execute('SELECT 1 FROM stylists WHERE id=?', (stylist,)).fetchone():
            return jsonify(error='Unknown stylist'), 400
        created_at = datetime.now().astimezone().isoformat()
        cur.execute('INSERT INTO bookings (stylist_id,date,time,customer_name,customer_phone,created_at) VALUES (?,?,?,?,?,?)',
                    (stylist,date,time,name.strip(),phone.strip(),created_at))
        conn.commit()
        return jsonify(id=cur.lastrowid, stylist_id=stylist, date=date, time=time), 201
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        if getattr(exc, 'sqlite_errorcode', None) == sqlite3.SQLITE_CONSTRAINT_UNIQUE:
            return jsonify(error='slot already booked'), 409
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=False)

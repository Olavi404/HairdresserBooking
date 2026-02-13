from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
# Allow overriding DB path for tests or custom locations
DB_PATH = os.environ.get('HAIR_DB') or os.path.join(BASE_DIR, 'data.db')

app = Flask(__name__, static_folder='static', template_folder='templates')


Tip: You can undo Copilot's changes to any point by clicking Restore Checkpoint.

now i have to create a domain so this porject is available and usable online


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
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
    cur.execute('SELECT id, stylist_id, date, time, customer_name, customer_phone, created_at FROM bookings ORDER BY date, time')
    rows = cur.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/admin/bookings')
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
def admin_delete_booking(booking_id):
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
    data = request.get_json() or {}
    required = ['stylist_id', 'date', 'time', 'customer_name', 'customer_phone']
    if not all(k in data for k in required):
        return jsonify({'error': 'missing fields'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''SELECT COUNT(*) as c FROM bookings WHERE stylist_id=? AND date=? AND time=?''', (data['stylist_id'], data['date'], data['time']))
    if cur.fetchone()['c'] > 0:
        conn.close()
        return jsonify({'error': 'slot already booked'}), 409

    created_at = datetime.utcnow().isoformat() + 'Z'
    cur.execute('''INSERT INTO bookings (stylist_id, date, time, customer_name, customer_phone, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)''', (data['stylist_id'], data['date'], data['time'], data['customer_name'], data['customer_phone'], created_at))
    conn.commit()
    booking_id = cur.lastrowid
    cur.execute('SELECT id, stylist_id, date, time, customer_name, customer_phone, created_at FROM bookings WHERE id=?', (booking_id,))
    row = cur.fetchone()
    conn.close()
    return jsonify(dict(row)), 201


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)

import os
import json
import tempfile

import pytest


def setup_module(module):
    # ensure tests use a temp DB
    fn = tempfile.NamedTemporaryFile(delete=False)
    fn.close()
    os.environ['HAIR_DB'] = fn.name


def teardown_module(module):
    path = os.environ.get('HAIR_DB')
    try:
        os.unlink(path)
    except Exception:
        pass


def test_endpoints():
    import app
    app.init_db()
    client = app.app.test_client()

    # stylists
    r = client.get('/api/stylists')
    assert r.status_code == 200
    stylists = r.get_json()
    assert isinstance(stylists, list) and len(stylists) >= 1

    # slots for stylist 1
    r = client.get('/api/slots?stylist_id=1')
    assert r.status_code == 200
    slots = r.get_json()
    assert isinstance(slots, list) and len(slots) > 0
    slot = slots[0]

    # book a slot
    payload = {
        'stylist_id': 1,
        'date': slot['date'],
        'time': slot['time'],
        'customer_name': 'Test User',
        'customer_phone': '123'
    }
    r = client.post('/api/book', data=json.dumps(payload), content_type='application/json')
    assert r.status_code == 201
    booking = r.get_json()
    assert 'customer_name' not in booking
    assert 'customer_phone' not in booking

    # conflict booking same slot
    r = client.post('/api/book', data=json.dumps(payload), content_type='application/json')
    assert r.status_code == 409

def test_admin_and_privacy(monkeypatch):
    import app
    from werkzeug.security import generate_password_hash
    monkeypatch.setenv('ADMIN_USERNAME', 'test-admin')
    monkeypatch.setenv('ADMIN_PASSWORD_HASH', generate_password_hash('test-password'))
    monkeypatch.setattr(app.app, 'secret_key', 'test-only-secret')
    client = app.app.test_client()
    assert client.get('/api/admin/bookings').status_code == 401
    assert client.get('/admin').status_code == 302
    assert client.get('/admin/login').status_code == 200
    with client.session_transaction() as s:
        token = s['csrf_token']
    assert client.post('/admin/login', data={'username':'test-admin','password':'wrong','csrf_token':token}).status_code == 401
    assert client.post('/admin/login', data={'username':'test-admin','password':'test-password','csrf_token':token}).status_code == 302
    assert client.get('/admin').status_code == 200
    bookings = client.get('/api/admin/bookings')
    assert bookings.status_code == 200
    assert bookings.headers['Cache-Control'] == 'no-store'
    for b in client.get('/api/bookings').get_json():
        assert 'customer_name' not in b and 'customer_phone' not in b
    assert client.delete('/api/admin/bookings/1').status_code == 403
    with client.session_transaction() as s:
        token = s['csrf_token']
    assert client.post('/admin/logout', data={'csrf_token':token}).status_code == 302
    assert client.get('/api/admin/bookings').status_code == 401

def test_concurrent_booking():
    import app
    from concurrent.futures import ThreadPoolExecutor
    slot = app.generate_slots(7)[-1]
    payload = dict(slot, stylist_id=2, customer_name='Test', customer_phone='123')
    def reserve():
        with app.app.test_client() as client:
            return client.post('/api/book', json=payload).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(lambda _: reserve(), range(2))) == [201, 409]

def test_login_rate_limit(monkeypatch):
    import app
    from werkzeug.security import generate_password_hash
    monkeypatch.setenv('ADMIN_USERNAME', 'admin')
    monkeypatch.setenv('ADMIN_PASSWORD_HASH', generate_password_hash('test'))
    monkeypatch.setattr(app.app, 'secret_key', 'test-only-secret')
    client = app.app.test_client()
    client.get('/admin/login', environ_overrides={'REMOTE_ADDR':'192.0.2.10'})
    with client.session_transaction() as s:
        token = s['csrf_token']
    for _ in range(5):
        assert client.post('/admin/login', data={'username':'admin','password':'bad','csrf_token':token}, environ_overrides={'REMOTE_ADDR':'192.0.2.10'}).status_code == 401
    response = client.post('/admin/login', data={'csrf_token':token}, environ_overrides={'REMOTE_ADDR':'192.0.2.10'})
    assert response.status_code == 429
    assert 'Retry-After' in response.headers

def test_unconfigured_admin_and_safe_template(monkeypatch):
    import app
    monkeypatch.delenv('ADMIN_USERNAME', raising=False)
    client = app.app.test_client()
    assert client.get('/admin/login').status_code == 503
    assert client.get('/api/admin/bookings').status_code == 401
    source = open(os.path.join(app.BASE_DIR,'templates','admin.html'), encoding='utf8').read()
    assert 'td.textContent = value' in source
    assert 'tr.innerHTML' not in source

def test_preflight_does_not_modify_database(tmp_path):
    import sqlite3
    from migration_preflight import inspect
    p = tmp_path / 'legacy.db'
    with sqlite3.connect(p) as db:
        db.execute('CREATE TABLE bookings(stylist_id INTEGER,date TEXT,time TEXT)')
        db.executemany('INSERT INTO bookings VALUES(?,?,?)', [(1,'2030-01-01','09:00')]*2)
    before = p.read_bytes()
    assert inspect(p)['duplicate_groups'] == 1
    assert p.read_bytes() == before

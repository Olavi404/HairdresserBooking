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
    assert booking['customer_name'] == 'Test User'

    # conflict booking same slot
    r = client.post('/api/book', data=json.dumps(payload), content_type='application/json')
    assert r.status_code == 409

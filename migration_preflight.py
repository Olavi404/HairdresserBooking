"""Read-only check before upgrading a legacy booking database."""
import argparse
import sqlite3
from pathlib import Path
from datetime import date, time

def inspect(path):
    path = Path(path).resolve()
    with sqlite3.connect(path.as_uri() + '?mode=ro', uri=True) as conn:
        duplicates = conn.execute('SELECT COUNT(*) FROM (SELECT 1 FROM bookings GROUP BY stylist_id,date,time HAVING COUNT(*) > 1)').fetchone()[0]
        invalid = 0
        for day, slot in conn.execute('SELECT date,time FROM bookings'):
            try:
                if date.fromisoformat(day).isoformat() != day or time.fromisoformat(slot).strftime('%H:%M') != slot:
                    invalid += 1
            except (ValueError, TypeError):
                invalid += 1
        foreign = len(conn.execute('PRAGMA foreign_key_check').fetchall())
        integrity = conn.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
    return {'duplicate_groups': duplicates, 'invalid_slots': invalid, 'foreign_key_violations': foreign, 'integrity_ok': integrity}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('database')
    result = inspect(parser.parse_args().database)
    print(result)
    raise SystemExit(0 if result['integrity_ok'] and not any(result[k] for k in ('duplicate_groups','invalid_slots','foreign_key_violations')) else 1)

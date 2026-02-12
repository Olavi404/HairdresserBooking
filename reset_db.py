import os
from pathlib import Path

DB = os.environ.get('HAIR_DB') or Path(__file__).parent / 'data.db'
if DB.exists():
    DB.unlink()

from app import init_db
init_db()
print(f'Recreated database at {DB}')

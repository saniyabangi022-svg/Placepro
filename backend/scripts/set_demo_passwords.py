"""PHASE 3 helper - run ONLY after the database is created in MySQL Workbench.
The sample data contains placeholder password hashes, so nobody could log in. This sets a real
bcrypt hash for every user:   python scripts/set_demo_passwords.py  [password]
(it only UPDATEs users.password_hash - the schema is not touched)"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rpms.util.db import session
from rpms.util.security import hash_password

pw = sys.argv[1] if len(sys.argv) > 1 else "Placepro@123"
with session() as cur:
    users = cur.all("SELECT user_id,username FROM users")
    for u in users:
        cur.run("UPDATE users SET password_hash=%s WHERE user_id=%s", (hash_password(pw), u["user_id"]))
print(f"Password set for {len(users)} users: {', '.join(u['username'] for u in users)}  (password: {pw})")

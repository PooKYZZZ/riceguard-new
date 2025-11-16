#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from db import get_db

db = get_db()
users = list(db.users.find())

print(f'Total users in database: {len(users)}\n')

for u in users:
    email = u.get('email', 'N/A')
    has_hash = 'passwordHash' in u
    hash_val = u.get('passwordHash', '')
    hash_valid = hash_val.startswith('$2b$') or hash_val.startswith('$2a$') if hash_val else False
    
    print(f"Email: {email}")
    print(f"  Has passwordHash field: {has_hash}")
    if has_hash:
        print(f"  Hash starts with: {hash_val[:10]}...")
        print(f"  Hash length: {len(hash_val)}")
        print(f"  Hash format valid: {hash_valid}")
    print()

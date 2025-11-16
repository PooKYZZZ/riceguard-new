#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug script to test login issue with tester123@gmail.com"""
import sys
import os

# Force UTF-8 output
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

sys.path.insert(0, '.')

from db import get_db
from security import verify_password

def test_login():
    db = get_db()
    user = db.users.find_one({'email': 'tester123@gmail.com'})
    
    if not user:
        print("[FAIL] User not found in database")
        return
    
    print(f"[OK] User found: {user['email']}")
    print(f"[OK] Name: {user.get('name')}")
    print(f"[OK] Password hash: {user['passwordHash'][:30]}...")
    print(f"[OK] Hash length: {len(user['passwordHash'])} characters")
    
    # Check hash format
    if user['passwordHash'].startswith('$2b$') or user['passwordHash'].startswith('$2a$'):
        print("[OK] Hash format is valid (bcrypt)")
    else:
        print(f"[FAIL] Hash format is INVALID: {user['passwordHash'][:10]}")
        return
    
    # Test password verification
    test_passwords = ['test123', 'Test123', 'Test123!', 'tester123']
    
    print("\n[TEST] Testing password verification:")
    for pwd in test_passwords:
        try:
            result = verify_password(pwd, user['passwordHash'])
            status = "[PASS]" if result else "[FAIL]"
            print(f"  {status} Password '{pwd}': {result}")
        except Exception as e:
            print(f"  [ERROR] Password '{pwd}': {type(e).__name__} - {e}")

if __name__ == "__main__":
    test_login()

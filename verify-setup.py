#!/usr/bin/env python3
"""Verify RiceGuard setup and configuration"""

import os
import sys
import platform
from pathlib import Path

# Color support for different platforms
class Colors:
    def __init__(self):
        self.is_windows = platform.system() == 'Windows'
        self.use_color = not self.is_windows
        if self.is_windows:
            try:
                import ctypes
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleOutputCP(65001)
                h_out = kernel32.GetStdHandle(-11)
                mode = ctypes.c_ulong()
                kernel32.GetConsoleMode(h_out, ctypes.byref(mode))
                kernel32.SetConsoleMode(h_out, mode | 0x0004)
                self.use_color = True
            except:
                self.use_color = False

    def __getattr__(self, name):
        colors = {
            'OKGREEN': '\033[92m',
            'FAIL': '\033[91m',
            'ENDC': '\033[0m'
        }
        return colors.get(name, '') if self.use_color else ''

# Safe print function for Windows
def safe_print(*args, **kwargs):
    """Print function that handles Unicode characters safely on Windows"""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Fallback: replace problematic characters
        text = ' '.join(str(arg) for arg in args)
        safe_text = text.encode('ascii', 'replace').decode('ascii')
        print(safe_text, **kwargs)

colors = Colors()

REPO_ROOT = Path(__file__).resolve().parent
BACKEND_DIR = REPO_ROOT / "backend"
FRONTEND_DIR = REPO_ROOT / "frontend"

def verify_setup():
    try:
        safe_print("[INFO] Verifying RiceGuard Setup...")

        # Check directories
        dirs_ok = all([
            BACKEND_DIR.exists(),
            FRONTEND_DIR.exists(),
            (BACKEND_DIR / ".venv").exists(),
            (FRONTEND_DIR / "node_modules").exists()
        ])

        # Check files
        files_ok = all([
            (BACKEND_DIR / ".env").exists(),
            (FRONTEND_DIR / ".env").exists()
        ])

        if dirs_ok and files_ok:
            safe_print(f"{colors.OKGREEN}[OK] Setup verification passed!{colors.ENDC}")
            return True
        else:
            safe_print(f"{colors.FAIL}[ERROR] Setup verification failed!{colors.ENDC}")
            if not dirs_ok:
                safe_print("Missing directories:")
                if not BACKEND_DIR.exists():
                    safe_print("  - backend/")
                if not FRONTEND_DIR.exists():
                    safe_print("  - frontend/")
                if not (BACKEND_DIR / ".venv").exists():
                    safe_print("  - backend/.venv (run setup.py)")
                if not (FRONTEND_DIR / "node_modules").exists():
                    safe_print("  - frontend/node_modules (run setup.py)")
            if not files_ok:
                safe_print("Missing files:")
                if not (BACKEND_DIR / ".env").exists():
                    safe_print("  - backend/.env (run setup.py)")
                if not (FRONTEND_DIR / ".env").exists():
                    safe_print("  - frontend/.env (run setup.py)")
            return False
    except Exception as e:
        safe_print(f"Unexpected error during verification: {e}")
        return False

if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)

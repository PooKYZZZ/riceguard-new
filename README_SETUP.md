# 🌾 RiceGuard Quick Setup Guide

Get RiceGuard running in minutes with our automated setup system!

## 🚀 One-Command Setup

### Windows Users
```bash
setup.bat
```

### macOS & Linux Users
```bash
./setup.sh
```

### Any Platform (Python Required)
```bash
python setup.py
```

## ✅ What the Setup Does Automatically

- **System Check**: Verifies Python 3.8+, Node.js 18+, and npm are installed
- **Dependencies**: Installs all backend and frontend dependencies
- **Environment**: Creates `.env.example` templates for configuration
- **Virtual Environment**: Sets up Python virtual environment
- **Directories**: Creates necessary directories (uploads, ml, scripts)
- **Safety**: Never overwrites existing files - your data is safe!

## 📋 Manual Steps After Setup

### 1. Configure MongoDB Atlas
1. Get a free cluster at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Copy environment template: `copy backend\.env.example backend\.env` (Windows) or `cp backend/.env.example backend/.env` (Linux/Mac)
3. Edit `backend/.env` with your MongoDB credentials
4. Generate JWT secret: `openssl rand -hex 32`

### 2. Start Development
```bash
python start-dev.py
```

This starts:
- Backend API: http://127.0.0.1:8000
- Frontend Web: http://localhost:3000
- API Documentation: http://127.0.0.1:8000/docs

### 3. Optional: Verify Setup
```bash
python verify-setup.py
```

## 🔧 System Requirements

- **Python 3.8+** - [Download Python](https://python.org)
- **Node.js 18+** - [Download Node.js](https://nodejs.org)
- **Git** (recommended) - [Download Git](https://git-scm.com)

## 🛠️ Troubleshooting

### Common Issues

**Python not found:**
- Windows: Reinstall Python and check "Add Python to PATH"
- macOS: `brew install python@3.9`
- Linux: `sudo apt install python3 python3-pip`

**Node.js not found:**
- Download from [nodejs.org](https://nodejs.org)
- macOS: `brew install node`
- Linux: Follow Node.js installation instructions

**Permission denied (Linux/Mac):**
```bash
chmod +x setup.sh
sudo ./setup.sh
```

**Dependencies failed to install:**
- Check internet connection
- Try running setup again
- Windows: Run as Administrator
- Linux/Mac: Try with `sudo`

### Need Help?

- 📖 **Documentation**: Read `CLAUDE.md` for detailed project info
- 🔍 **Verify Setup**: Run `python verify-setup.py`
- 🐛 **Issues**: Check the error output above for specific guidance

## 🎯 Quick Start Summary

```bash
# 1. Clone the repository
git clone <repository-url>
cd riceguard

# 2. Run setup (choose your platform)
setup.bat          # Windows
./setup.sh         # macOS/Linux
python setup.py    # Any platform

# 3. Configure environment
copy backend\.env.example backend\.env  # Windows
# Edit backend\.env with MongoDB Atlas credentials

# 4. Start development
python start-dev.py

# 5. Open browser
# Frontend: http://localhost:3000
# API Docs: http://127.0.0.1:8000/docs
```

## 🏆 Success!

When setup completes successfully, you'll see:
- ✅ All dependencies installed
- ✅ Virtual environment created
- ✅ Environment templates ready
- ✅ Development servers running

Your RiceGuard development environment is ready for coding! 🚀
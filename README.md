# RiceGuard

Multi-platform rice leaf disease detection system using FastAPI, React, and TensorFlow.

## Quick Start (2 minutes)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd riceguard

# 2. Run setup (one-time)
python setup.py                    # Cross-platform automated setup

# 3. Configure environment files
# Edit backend/.env and add your MongoDB Atlas credentials:
# mongodb+srv://<username>:<password>@<cluster>.mongodb.net/riceguard_db
# Get free cluster: https://www.mongodb.com/cloud/atlas

# 4. Start development servers
python start.py                    # Start both backend and frontend
```

## Access Points

- 🌐 **Frontend**: http://localhost:3000
- 🔧 **Backend API**: http://127.0.0.1:8000
- 📚 **API Docs**: http://127.0.0.1:8000/docs

## Architecture

**Backend**: FastAPI + MongoDB Atlas + TensorFlow
**Frontend**: React with JWT authentication
**Mobile**: React Native (Expo) with TensorFlow Lite
**ML**: 6 disease classes with confidence calibration

## Project Structure

```
riceguard/
├── setup.py          # One-command automated setup
├── start.py          # Start all development services
├── README.md         # This file
├── .gitignore        # Git ignore rules
├── backend/          # FastAPI application
├── frontend/         # React application
├── mobileapp/        # React Native application
├── ml/               # ML model assets
├── docs/             # Documentation
├── tools/            # Development utilities
└── scripts/          # Build and deployment scripts
```

## ML Disease Classes

- bacterial_leaf_blight
- brown_spot
- healthy
- leaf_blast
- leaf_scald
- narrow_brown_spot

## Development

For daily development, run:
```bash
python start.py
```

For verification and testing:
```bash
python tools/verify-setup.py
```

## Team 27

- Mark Angelo Aquino - Team Lead
- Faron Jabez Nonan - Frontend
- Froilan Gayao - Backend
- Eugene Dela Cruz - ML
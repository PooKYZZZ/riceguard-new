# RiceGuard

Multi-platform rice leaf disease detection system using FastAPI, React, and TensorFlow.

## Quick Start (2 minutes)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd riceguard

# 2. Run setup (one-time)
setup/setup.bat                    # Windows
chmod +x setup/setup.sh && ./setup/setup.sh  # macOS/Linux
python setup/setup.py              # Cross-platform Python

# 3. Configure environment files
cp setup/environment/backend.env.example backend/.env
cp setup/environment/frontend.env.example frontend/.env

# 4. Add MongoDB Atlas credentials
# Edit backend/.env and replace:
# mongodb+srv://<username>:<password>@<cluster>.mongodb.net/riceguard_db
# Get free cluster: https://www.mongodb.com/cloud/atlas

# 5. Start development servers
python start-dev.py                # Start both backend and frontend
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
├── README.md         # This file
├── .gitignore        # Git ignore rules
├── setup/            # Complete setup system
│   ├── setup.py      # Cross-platform setup
│   ├── setup.bat     # Windows setup
│   ├── setup.sh      # Unix/Linux setup
│   └── environment/  # Environment templates
├── scripts/          # Utility scripts
├── backend/          # FastAPI application
├── frontend/         # React application
├── mobileapp/        # React Native application
├── ml/               # ML model assets
└── tools/            # Utility scripts
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
python start-dev.py
```

For verification and testing:
```bash
python verify-setup.py
```

## Team 27

- Mark Angelo Aquino - Team Lead
- Faron Jabez Nonan - Frontend
- Froilan Gayao - Backend
- Eugene Dela Cruz - ML
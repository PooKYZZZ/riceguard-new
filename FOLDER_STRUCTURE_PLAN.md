# RiceGuard Folder Structure Redesign Plan

## Executive Summary

This document outlines the redesign of the RiceGuard project folder structure for better organization, maintainability, and professional appearance.

## Current Issues Identified

1. **Backup files in root**: `setup-dangerous.bat.backup`, `setup-dangerous.py.backup`
2. **Orphaned files**: `App.css` (appears to be leftover)
3. **Temporary directories**: `tmp_pymongo`, `__pycache__`, `uploads` in root
4. **Documentation scattered**: Multiple .md files in root directory
5. **Configuration files**: `.env` in root instead of backend-specific

## New Target Structure

```
riceguard/                          # Clean root with only essential files
├── README.md                      # Main project documentation
├── CLAUDE.md                      # Claude AI development guide
├── .gitignore                     # Git ignore rules
├── dev_runner.py                  # Development runner script
├── start-dev.py                   # Development startup script
├── verify-setup.py                # Setup verification script
│
├── setup/                         # All setup and installation files
│   ├── setup.py                   # Main Python setup script
│   ├── setup.bat                  # Windows batch setup
│   ├── setup.sh                   # Unix/Linux shell setup
│   ├── setup-safe.py              # Safe setup variant
│   ├── requirements.txt           # Python dependencies
│   └── environment/               # Environment configuration templates
│       ├── backend.env.example    # Backend environment template
│       └── frontend.env.example   # Frontend environment template
│
├── docs/                          # All documentation
│   ├── SETUP_REDESIGN_SUMMARY.md  # Setup documentation
│   ├── README_SETUP.md           # Setup instructions
│   ├── TROUBLESHOOTING.md        # Troubleshooting guide
│   ├── TEST_RESULTS.md           # Test results
│   └── API/                      # API documentation
│       └── (auto-generated docs)
│
├── scripts/                       # Utility and maintenance scripts
│   ├── setup-database.py         # Database setup
│   ├── setup-ml-model.py         # ML model setup
│   └── setup-mobile.py           # Mobile app setup
│
├── backend/                       # Backend application
│   ├── main.py                   # FastAPI application
│   ├── routers.py                # API routes
│   ├── models.py                 # Pydantic models
│   ├── db.py                     # Database connection
│   ├── ml_service.py             # ML integration
│   ├── storage.py                # File handling
│   ├── requirements.txt          # Backend dependencies
│   ├── .env                      # Backend environment (local)
│   └── uploads/                  # File upload directory
│       └── (user uploads)
│
├── frontend/                      # Frontend application
│   ├── src/                      # React source code
│   ├── public/                   # Static assets
│   ├── package.json              # Node.js dependencies
│   ├── .env                      # Frontend environment (local)
│   └── build/                    # Production build output
│
├── ml/                           # Machine learning assets
│   ├── model.h5                  # Trained model (128MB - not in git)
│   ├── model_metadata.json       # Model configuration
│   └── calibration_data.json     # Confidence calibration data
│
├── mobileapp/                    # Mobile application
│   ├── (React Native project)
│   └── (mobile-specific files)
│
└── RiceGuard_Full_Project_Context.md  # Complete project context
```

## File Moves and Changes

### Files to Remove
- `setup-dangerous.bat.backup` - backup file
- `setup-dangerous.py.backup` - backup file
- `App.css` - orphaned frontend file
- `tmp_pymongo/` - temporary directory
- `__pycache__/` - Python cache (auto-generated)

### Files to Move
- `.env` → `backend/.env`
- `uploads/` → `backend/uploads/`
- `README_SETUP.md` → `docs/`
- `SETUP_REDESIGN_SUMMARY.md` → `docs/`
- `TROUBLESHOOTING.md` → `docs/`
- `TEST_RESULTS.md` → `docs/`
- `setup-database.py` → `scripts/`
- `setup-ml-model.py` → `scripts/`
- `setup-mobile.py` → `scripts/`

### Files to Keep in Root
- `README.md` - Main project documentation
- `CLAUDE.md` - AI development guide
- `.gitignore` - Git ignore rules
- `dev_runner.py` - Development runner
- `start-dev.py` - Development startup
- `verify-setup.py` - Setup verification
- `RiceGuard_Full_Project_Context.md` - Complete project context

## Path Updates Required

### Script Updates
1. **dev_runner.py** - Update relative paths to backend/frontend
2. **setup.py** - Update paths for file operations
3. **start-dev.py** - Update startup paths
4. **verify-setup.py** - Update verification paths

### Backend Updates
1. **main.py** - Update static file paths for uploads
2. **storage.py** - Update upload directory paths
3. **db.py** - Update any file references

### Frontend Updates
1. **package.json** - Update any relative paths
2. **API calls** - Verify backend endpoint URLs

## Implementation Steps

1. **Create new directory structure**
2. **Move files to appropriate locations**
3. **Update all script paths and references**
4. **Remove backup and temporary files**
5. **Test setup functionality with new structure**
6. **Commit and push changes**

## Benefits of New Structure

1. **Clean Root Directory**: Only essential files in root
2. **Logical Organization**: Related files grouped together
3. **Professional Appearance**: Industry-standard structure
4. **Better Maintainability**: Easier to find and update files
5. **Clear Separation**: Distinct concerns in different directories
6. **Scalable Structure**: Easy to add new components

## Cross-Platform Compatibility

- Maintain both Windows (.bat) and Unix (.sh) setup scripts
- Use Python for cross-platform utilities
- Ensure path separators work across platforms
- Preserve existing functionality in new structure
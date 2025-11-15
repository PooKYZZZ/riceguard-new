# RiceGuard Troubleshooting Guide

## 🚨 Quick Start Checklist

Before diving into troubleshooting, ensure you've completed these essential steps:

- [ ] **System Requirements**: Python 3.8+, Node.js 18+, Git installed
- [ ] **Setup Script**: Run `python setup.py` first
- [ ] **Environment Files**: Copy `.env.example` to `.env` and configure
- [ ] **ML Model**: Download and place `ml/model.h5` (128MB)
- [ ] **Database**: Run `python scripts/setup-database.py`
- [ ] **Dependencies**: All Python packages and npm modules installed

## 🔧 Common Issues & Solutions

### Backend Issues

#### Port 8000 Already in Use

**Problem**: `OSError: [Errno 48] Address already in use`

```bash
# Windows (PowerShell)
netstat -ano | findstr :8000
# Note the PID, then kill it
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8000
# Note the PID, then kill it
kill -9 <PID>

# Alternative: Use different port
python -m uvicorn main:app --port 8001
```

#### MongoDB Connection Failed

**Problem**: `pymongo.errors.ServerSelectionTimeoutError`

**Causes & Solutions**:

1. **Wrong Connection String**
   ```env
   # Correct format:
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/dbname
   ```

2. **IP Whitelist Issue**
   - Go to MongoDB Atlas → Network Access
   - Add your current IP: https://whatismyipaddress.com/
   - For development, you can add `0.0.0.0/0` (less secure)

3. **Authentication Issues**
   - Verify username/password are correct
   - Check database user permissions
   - Ensure user has read/write access

4. **Network Issues**
   - Check internet connection
   - Try different network
   - Disable VPN temporarily

#### TensorFlow Not Found

**Problem**: `ModuleNotFoundError: No module named 'tensorflow'`

```bash
# Activate virtual environment first
cd backend

# Windows
.venv\\Scripts\\Activate.ps1

# macOS/Linux
source .venv/bin/activate

# Verify activation (should show (.venv) in prompt)
# Reinstall dependencies
pip install -r requirements.txt

# If still fails, try fresh install
pip install --upgrade pip
pip install tensorflow==2.20.0
```

#### ML Model Loading Error

**Problem**: `FileNotFoundError` or model loading failures

**Solutions**:

1. **Check Model File**
   ```bash
   # Verify model exists
   ls -la ml/model.h5

   # Check file size (should be ~128MB)
   du -h ml/model.h5
   ```

2. **Download Model**
   ```bash
   python scripts/download-model.py
   ```

3. **Validate Model Path**
   ```env
   # In backend/.env
   MODEL_PATH=../ml/model.h5
   ```

#### Virtual Environment Issues

**Problem**: Activation fails or packages not found

```bash
# Create new virtual environment
cd backend
python -m venv .venv

# Activate
# Windows
.venv\\Scripts\\Activate.ps1

# macOS/Linux
source .venv/bin/activate

# Reinstall dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Frontend Issues

#### Port 3000 Already in Use

```bash
# Kill existing process
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :3000
kill -9 <PID>

# Or use different port
npm start -- --port=3001
```

#### npm Install Fails

**Problem**: Dependency installation errors

```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and lock file
rm -rf node_modules package-lock.json

# Reinstall
npm install

# If still fails, try:
npm install --legacy-peer-deps
```

#### CORS Errors in Browser

**Problem**: `Access-Control-Allow-Origin` errors

**Solution**: Update backend CORS settings

```env
# In backend/.env
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
```

Then restart the backend server.

#### React Build Fails

**Problem**: TypeScript errors or build failures

```bash
# Check for TypeScript errors
npm run build

# Clear cache
npm run build -- --reset-cache

# Update dependencies
npm update
```

### Mobile App Issues

#### Expo Go Cannot Connect to Backend

**Problem**: Network connection errors on mobile app

**Solutions**:

1. **Backend Host Configuration**
   ```bash
   # Start backend with --host 0.0.0.0
   python -m uvicorn main:app --host 0.0.0.0 --port 8000
   ```

2. **Find Your PC IP**
   ```bash
   # Windows
   ipconfig
   # Look for IPv4 Address (e.g., 192.168.1.100)

   # macOS/Linux
   ifconfig | grep "inet "
   ```

3. **Configure Mobile App**
   ```bash
   # Set environment variable
   export EXPO_PUBLIC_API_BASE_URL="http://YOUR_PC_IP:8000/api/v1"

   # Start Expo
   npx expo start --lan --clear
   ```

4. **Firewall Issues**
   - Windows: Allow ports 8000 and 8081 in Windows Firewall
   - macOS: Allow Node.js in Security & Privacy settings

#### Metro Bundler Issues

**Problem**: Bundle build failures or cache issues

```bash
# Clear Metro cache
npx expo start --clear

# Clear all caches
npx expo start -c

# Reset npm cache
npm start -- --reset-cache

# If issues persist, clear node_modules
rm -rf node_modules
npm install
```

#### QR Code Not Working

**Problem**: Expo Go can't scan QR code

**Solutions**:

1. **Use LAN Mode**
   ```bash
   npx expo start --lan
   ```

2. **Use Tunnel Mode** (if LAN doesn't work)
   ```bash
   npx expo start --tunnel
   ```

3. **Manual Connection**
   - Find the URL in terminal (e.g., `exp://192.168.1.100:8081`)
   - Type it directly in Expo Go

### Environment Setup Issues

#### .env Files Not Working

**Problem**: Environment variables not loaded

**Solutions**:

1. **Check File Location**
   ```bash
   # Backend
   backend/.env

   # Frontend
   frontend/.env
   ```

2. **Verify File Format**
   ```env
   # No spaces around =
   VARIABLE=value
   # NOT:
   VARIABLE = value
   ```

3. **Check File Encoding**
   - Use UTF-8 encoding
   - Avoid BOM (Byte Order Mark)

#### Permission Issues

**Windows**:
```powershell
# Set execution policy for PowerShell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run as Administrator if needed
```

**macOS/Linux**:
```bash
# Fix npm permissions
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) /usr/local/lib/node_modules

# Fix Python permissions
chmod +x scripts/*.py
```

### Database Issues

#### Database Connection Timeout

**Problem**: Connection to MongoDB Atlas times out

**Solutions**:

1. **Check Internet Connection**
   - Test with: `ping mongodb.com`
   - Try different network

2. **Verify Connection String**
   - Copy directly from MongoDB Atlas
   - Replace placeholder values

3. **Test with MongoDB Compass**
   - Use GUI tool to test connection
   - Same connection string as backend

#### Database Index Creation Failed

**Problem**: Index creation errors during setup

```bash
# Run database setup manually
python scripts/setup-database.py

# Check MongoDB logs in Atlas
# Verify user has admin privileges
```

### Performance Issues

#### Slow Development Server

**Solutions**:

1. **Increase Node.js Memory**
   ```bash
   export NODE_OPTIONS="--max-old-space-size=4096"
   npm start
   ```

2. **Use SSD Storage**
   - Move project to SSD
   - Avoid network drives

3. **Close Unnecessary Apps**
   - Free up RAM and CPU
   - Close browser tabs

#### Large npm Install Times

```bash
# Use npm registry mirror
npm config set registry https://registry.npm.taobao.org/

# Or use yarn (faster)
npm install -g yarn
yarn install
```

## 🖥️ Platform-Specific Solutions

### Windows

#### PowerShell Execution Policy
```powershell
# Allow script execution
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Check current policy
Get-ExecutionPolicy
```

#### Windows Firewall
```powershell
# Allow Node.js through firewall
New-NetFirewallRule -DisplayName "Node.js" -Direction Inbound -Port 3000,8000,8081 -Protocol TCP -Action Allow
```

#### Antivirus Issues
- Add project folder to antivirus exceptions
- Allow Node.js and Python executables
- Temporarily disable real-time protection

### macOS

#### Homebrew Dependencies
```bash
# Install via Homebrew
brew install python@3.9 node mongodb-community

# Fix permissions
sudo xcode-select --install
```

#### Keychain Issues
```bash
# Reset npm credentials
npm logout
npm login

# Clear keychain access for Node.js
```

### Linux

#### Package Dependencies
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv nodejs npm build-essential

# CentOS/RHEL
sudo yum install python3 python3-pip nodejs npm gcc-c++
```

#### Permission Issues
```bash
# Fix npm global packages
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.bashrc
```

## 🧪 Testing & Debugging

### Backend Testing

```bash
# Test API endpoints
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/docs

# Test database connection
python -c "from db import get_database; print(get_database())"

# Test ML model
python -c "from ml_service import MLService; print(MLService())"
```

### Frontend Testing

```bash
# Test React app build
npm run build

# Test in different browsers
# Chrome, Firefox, Safari, Edge

# Check browser console for errors
# F12 → Console tab
```

### Mobile Testing

```bash
# Test with different devices
# Android phone, iPhone, tablet

# Test network connectivity
# Ping backend from mobile device browser
```

## 🆘 Getting Help

### Debug Information Collection

When reporting issues, include:

1. **System Information**
   ```bash
   # System info
   python --version
   node --version
   npm --version

   # OS info
   # Windows: systeminfo
   # macOS: sw_vers
   # Linux: uname -a
   ```

2. **Error Messages**
   - Full error traceback
   - Steps to reproduce
   - Expected vs actual behavior

3. **Configuration**
   - .env file contents (remove sensitive data)
   - Package versions
   - Network setup

### Community Resources

1. **GitHub Issues**: Search existing issues first
2. **Team Communication**: Discord/Slack channels
3. **Documentation**:
   - FastAPI: https://fastapi.tiangolo.com/
   - React: https://reactjs.org/docs/
   - Expo: https://docs.expo.dev/
   - MongoDB Atlas: https://docs.atlas.mongodb.com/

### Quick Commands Reference

```bash
# Setup
python setup.py
python scripts/setup-database.py
python scripts/setup-ml-model.py

# Development
python start-dev.py
python verify-setup.py

# Troubleshooting
python scripts/download-model.py
python scripts/convert-to-tflite.py

# Manual testing
cd backend && python -m uvicorn main:app --reload
cd frontend && npm start
cd mobileapp/riceguard && npx expo start
```

---

## 🎯 Pro Tips

1. **Regular Updates**: Keep dependencies updated weekly
2. **Backup Configuration**: Save working .env files
3. **Version Control**: Commit .env.example, ignore .env
4. **Documentation**: Keep notes of working configurations
5. **Team Communication**: Share solutions with teammates

Remember: Most issues are configuration-related. Double-check environment files and network settings before assuming code problems.
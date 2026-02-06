# Git Setup Instructions

Due to permission restrictions, please run these Git commands manually in your terminal:

## 1. Initialize Git (if not already initialized)

```bash
cd /Users/user/AI_Autonomous_Engergy_grid_and_smart_battery_management_systems
git init
```

## 2. Add Remote Repository

```bash
git remote add origin https://github.com/Web8080/Energy-Grid-and-Battery-Management-System.git
```

Or if remote already exists:
```bash
git remote set-url origin https://github.com/Web8080/Energy-Grid-and-Battery-Management-System.git
```

## 3. Stage All Files (excluding .env and sensitive files)

```bash
git add .
```

The `.gitignore` file will automatically exclude:
- `.env` files
- `.cursor/rules/` folder
- Secrets, API keys, logs
- Database files
- Other sensitive files

## 4. Create Initial Commit

```bash
git commit -m "Initial commit: Energy Grid & Battery Management System

- Complete system architecture and design
- Cloud backend API (FastAPI)
- Device fleet daemon (Raspberry Pi)
- ML pipeline for schedule optimization
- Authentication and authorization system
- Security hardening and audit fixes
- Observability stack (Prometheus/Grafana)
- CI/CD pipeline configuration
- Comprehensive documentation"
```

## 5. Push to GitHub

```bash
git branch -M main
git push -u origin main
```

If you encounter authentication issues, you may need to:
- Use a personal access token instead of password
- Set up SSH keys
- Configure Git credentials

## Verify What Will Be Committed

Before pushing, verify sensitive files are excluded:

```bash
git status
git ls-files | grep -E "\.env|SECRET|PASSWORD|API_KEY"
```

If any sensitive files appear, they're already in `.gitignore` but check to be sure.

## Files Excluded from Git

The following are automatically excluded (in `.gitignore`):
- ✅ `.env` and all `.env.*` files
- ✅ `.cursor/rules/` folder
- ✅ All secrets, API keys, passwords
- ✅ Log files
- ✅ Database files (*.db, *.sqlite)
- ✅ ML model files (*.pkl)
- ✅ Node modules
- ✅ System logs

---

**Important**: Never commit the `.env` file or any files containing secrets!

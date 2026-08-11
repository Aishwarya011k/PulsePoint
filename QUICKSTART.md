# 🚀 PulsePoint Phase 1 - Quick Start Guide

All dependencies are installed and the database is configured. You're ready to run!

## Open 3 Terminal Windows

### Terminal 1: Backend API

```bash
cd backend-api
source venv/bin/activate
python main.py
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ Visit http://localhost:8000/docs to see the interactive API documentation

---

### Terminal 2: Prober Worker

```bash
cd prober-worker
source venv/bin/activate
python worker.py
```

**Expected Output:**
```
2026-08-11 12:00:00 - __main__ - INFO - Starting PulsePoint Prober Worker
2026-08-11 12:00:00 - __main__ - INFO - Scheduler started - will check targets every 60s
```

✅ Watch this terminal to see health checks running every 60 seconds

---

### Terminal 3: Frontend

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
  VITE v5.0.8  ready in 234 ms

  ➜  Local:   http://localhost:3000/
  ➜  Press h to show help
```

✅ Visit http://localhost:3000/ to see the dashboard

---

## First Steps

1. **Register an account** at http://localhost:3000/
   - Email: anything@example.com
   - Password: anything

2. **Add a target** in the dashboard
   - Name: "httpbin"
   - URL: `https://httpbin.org/status/200`
   - Interval: 60 seconds

3. **Wait for first check** (watch prober-worker terminal)
   - You'll see: "Check successful for https://httpbin.org/status/200"

4. **Refresh dashboard** and click your target
   - You'll see the check result: ✅ 200 status, response time

5. **Try a manual check**
   - Click "Check Now" button
   - See instant results

---

## Test the API

Once backend is running, test it with curl:

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# Response (save the token):
# {"access_token":"eyJ...","token_type":"bearer"}

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'

# List targets (replace TOKEN with your access_token)
curl http://localhost:8000/targets \
  -H "Authorization: Bearer TOKEN"

# Create a target
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "name": "My API",
    "url": "https://api.example.com/health",
    "check_interval_seconds": 300
  }'
```

---

## Run Tests

In a new terminal:

```bash
cd backend-api
source venv/bin/activate
pytest test_main.py -v
```

Expected: **8/8 tests pass** ✅

---

## Troubleshooting

### "Connection refused" when starting backend

**Issue:** Backend can't connect to PostgreSQL

**Solution:**
```bash
# Verify Postgres is running
psql -h localhost -U pulse_user -d pulsepoint

# If it fails, start PostgreSQL:
# On macOS: brew services start postgresql
# On Linux: sudo service postgresql start
# Or with Docker: docker start pulsepoint-db
```

### "Address already in use"

Port is taken. Change it in `.env`:

**Backend:** Edit `backend-api/.env`, change `API_PORT=8000` to `API_PORT=8001`

**Frontend:** Edit `frontend/vite.config.ts`, change `port: 3000` to `port: 3001`

### Frontend can't connect to API

1. Make sure backend is running
2. Check `frontend/.env` has correct `VITE_API_BASE_URL`
3. Check browser console (F12) for CORS errors

### Worker not checking targets

1. Check database connection: `psql -h localhost -U pulse_user -d pulsepoint`
2. Verify targets exist: `curl http://localhost:8000/targets -H "Authorization: Bearer TOKEN"`
3. Check that 60 seconds have passed since adding the target

---

## Environment Files

### backend-api/.env

```
DATABASE_URL=postgresql://pulse_user:pulse_password@localhost:5432/pulsepoint
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_PORT=8000
API_HOST=0.0.0.0
```

### prober-worker/.env

```
DATABASE_URL=postgresql://pulse_user:pulse_password@localhost:5432/pulsepoint
```

### frontend/.env

```
VITE_API_BASE_URL=http://localhost:8000
```

---

## What's Running

- **Backend API (FastAPI)** on http://localhost:8000
  - REST endpoints for auth, targets, checks
  - Auto-creates PostgreSQL tables on startup
  
- **Prober Worker (APScheduler)**
  - Runs every 60 seconds
  - Checks all targets that are due
  - Records results in database
  - Auto-manages incidents

- **Frontend (React + Vite)** on http://localhost:3000
  - User registration/login
  - Target management
  - View check results and history
  - Trigger manual checks

- **PostgreSQL Database**
  - Stores users, targets, checks, incidents
  - All three services share this database

---

## Key Features

✅ User authentication with JWT
✅ Register and manage monitoring targets
✅ Automatic scheduled health checks
✅ Manual check triggering
✅ Incident tracking (opens when service down, closes when back up)
✅ Check history and statistics
✅ Responsive dashboard

---

## Next Steps

- Try adding multiple targets
- Test failure scenarios (point to a bad URL)
- Watch incidents auto-open and resolve
- Explore the API at http://localhost:8000/docs
- Run the test suite: `pytest test_main.py -v`

---

## Questions?

Refer to:
- API docs: http://localhost:8000/docs (interactive OpenAPI)
- [PHASE1_SETUP.md](PHASE1_SETUP.md) for detailed setup
- [README.md](README.md) for architecture and vision

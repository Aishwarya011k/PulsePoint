# PulsePoint Phase 1 — Local Setup Guide

This guide walks through setting up and running **Phase 1** of PulsePoint: a working local monitoring application with no Docker, Kubernetes, or DevOps infrastructure.

## What Phase 1 Includes

✅ User authentication (JWT-based)
✅ Target registration and management
✅ Scheduled health checks (HTTP GET/HEAD)
✅ Incident tracking (open/resolved)
✅ React dashboard with real-time status
✅ Pytest tests for the API

## Architecture

```
Frontend (React)        Backend API (FastAPI)        Prober Worker (Python)
   :3000      ◀─────────    :8000        ◄─────────────────┐
              JSON API              SQL queries              │
                               │                        Every 60s:
                               ▼                        - Query targets
                            PostgreSQL ────────────────► - Check URLs
                                                        - Record results
```

## Prerequisites

### 1. PostgreSQL

Install PostgreSQL 15+ locally or use Docker:

**Option A: Docker (Quick)**
```bash
docker run --name pulsepoint-db \
  -e POSTGRES_USER=pulse_user \
  -e POSTGRES_PASSWORD=pulse_password \
  -e POSTGRES_DB=pulsepoint \
  -p 5432:5432 \
  -d postgres:15
```

**Option B: Native Install (macOS with Homebrew)**
```bash
brew install postgresql
brew services start postgresql
createdb pulsepoint
createuser pulse_user -P  # Set password to: pulse_password
```

**Option C: Native Install (Linux/Ubuntu)**
```bash
sudo apt-get install postgresql postgresql-contrib
sudo -u postgres psql <<EOF
CREATE DATABASE pulsepoint;
CREATE USER pulse_user WITH PASSWORD 'pulse_password';
ALTER ROLE pulse_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE pulsepoint TO pulse_user;
EOF
```

### 2. Python 3.11+

```bash
python3 --version  # Should be 3.11+
```

### 3. Node.js 18+

```bash
node --version  # Should be 18+
npm --version
```

### 4. Test Database Connection

```bash
psql -h localhost -U pulse_user -d pulsepoint
# Type password: pulse_password
# Type \q to exit
```

## Setup & Run

### Step 1: Backend API

```bash
cd backend-api

# Copy environment template
cp .env.example .env

# Verify .env (should match your PostgreSQL setup):
# DATABASE_URL=postgresql://pulse_user:pulse_password@localhost:5432/pulsepoint
# JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
# API_PORT=8000

# Install dependencies
pip install -r requirements.txt

# Run the server (will create tables on startup)
python main.py
```

Expected output:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

✅ API is ready. Visit http://localhost:8000/docs for interactive API docs.

### Step 2: Prober Worker

In a new terminal:

```bash
cd prober-worker

# Copy environment template
cp .env.example .env

# Verify .env (should match backend):
# DATABASE_URL=postgresql://pulse_user:pulse_password@localhost:5432/pulsepoint

# Install dependencies
pip install -r requirements.txt

# Run the worker
python worker.py
```

Expected output:
```
2026-08-11 12:00:00 - __main__ - INFO - Starting PulsePoint Prober Worker
2026-08-11 12:00:00 - __main__ - INFO - Scheduler started - will check targets every 60s
```

✅ Worker is running. It will log check activities every 60 seconds.

### Step 3: Frontend

In a new terminal:

```bash
cd frontend

# Copy environment template
cp .env.example .env

# Verify .env:
# VITE_API_BASE_URL=http://localhost:8000

# Install dependencies
npm install

# Run dev server
npm run dev
```

Expected output:
```
  VITE v5.0.8  ready in 234 ms

  ➜  Local:   http://localhost:3000/
  ➜  Press h to show help
```

✅ Frontend is ready at http://localhost:3000/

## First Run Walkthrough

### 1. Create an Account

1. Open http://localhost:3000/
2. Click "Register here"
3. Enter email (e.g., `test@example.com`) and password (e.g., `password123`)
4. Click "Register"
5. You'll be logged in and see the dashboard

### 2. Add a Target

1. Click the "+ Add" button on the left
2. Fill in:
   - **Target Name:** `httpbin` (or any name)
   - **URL:** `https://httpbin.org/status/200` (or any HTTP endpoint)
   - **Check Interval:** `60` seconds (default is 300)
3. Click "Add Target"

Target appears in the list on the left.

### 3. Wait for First Check

The Prober Worker checks every 60 seconds. Watch the terminal running `worker.py`:

```
2026-08-11 12:05:00 - __main__ - INFO - Starting health check cycle
2026-08-11 12:05:00 - __main__ - INFO - Found 1 targets to check
2026-08-11 12:05:00 - __main__ - INFO - Checking target 1: httpbin (https://httpbin.org/status/200)
2026-08-11 12:05:00 - __main__ - INFO - Check successful for https://httpbin.org/status/200: status=200, time=234.5ms
2026-08-11 12:05:00 - __main__ - INFO - Check recorded for target 1
2026-08-11 12:05:00 - __main__ - INFO - Health check cycle completed
```

### 4. View Results

Refresh the dashboard (http://localhost:3000/) and click on your target. You should see:

- **Current Status:** 🟢 (green = OK)
- **Response Time:** e.g., `234ms`
- **Status Code:** `200`
- **Recent Checks table:** Your first check appears here

### 5. Manual Check

Click "Check Now" to trigger an immediate health check (doesn't wait 60s). Results appear instantly in the Recent Checks table.

### 6. Test Failure Handling

1. Create another target with a URL that fails, e.g., `https://httpbin.org/status/500`
2. Click "Check Now"
3. Result shows 🔴 (red = DOWN) with status code `500`
4. Worker automatically creates an "incident" record (you'll see it in the check history)
5. If you fix it (e.g., change URL to 200), the incident will auto-resolve on the next successful check

## API Usage

### Login & Get Token

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Create a Target

```bash
curl -X POST http://localhost:8000/targets \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -d '{
    "name": "My API",
    "url": "https://api.example.com/health",
    "check_interval_seconds": 300
  }'
```

### List Targets

```bash
curl http://localhost:8000/targets \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### Trigger Manual Check

```bash
curl -X POST http://localhost:8000/targets/1/check-now \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### View Check History

```bash
curl "http://localhost:8000/targets/1/checks?limit=10&offset=0" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

See http://localhost:8000/docs for full OpenAPI documentation with interactive try-it-out.

## Testing

Run the backend test suite:

```bash
cd backend-api
pytest test_main.py -v
```

Expected output:
```
test_main.py::test_register PASSED
test_main.py::test_register_duplicate_email PASSED
test_main.py::test_login PASSED
test_main.py::test_login_invalid_credentials PASSED
test_main.py::test_create_target PASSED
test_main.py::test_list_targets PASSED
test_main.py::test_delete_target PASSED
test_main.py::test_unauthorized_access PASSED

========================== 8 passed in 0.50s ==========================
```

## Environment Variables

### Backend API (backend-api/.env)

```
# Database
DATABASE_URL=postgresql://pulse_user:pulse_password@localhost:5432/pulsepoint

# JWT Configuration
JWT_SECRET=your_super_secret_jwt_key_change_this_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Server
API_PORT=8000
API_HOST=0.0.0.0
```

**In Production:** Change `JWT_SECRET` to a strong random string.

### Prober Worker (prober-worker/.env)

```
# Database (must match backend)
DATABASE_URL=postgresql://pulse_user:pulse_password@localhost:5432/pulsepoint
```

### Frontend (frontend/.env)

```
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000
```

## Troubleshooting

### "psycopg2: connection refused"

Backend can't reach Postgres. Check:

```bash
# Test connection directly:
psql -h localhost -U pulse_user -d pulsepoint
# Type password when prompted

# Check DATABASE_URL in backend-api/.env matches your setup
```

### "Address already in use"

Port is already taken. Either:
- Kill the process using the port, or
- Change the port in the service's `.env`:

```bash
# For backend (change API_PORT in backend-api/.env)
API_PORT=8001

# For frontend (change port in frontend/vite.config.ts)
port: 3001,
```

### "Worker not checking targets"

Check the worker terminal for errors:

1. Ensure database connection is working (same `DATABASE_URL`)
2. Verify targets exist: `curl http://localhost:8000/targets -H "Authorization: Bearer <TOKEN>"`
3. Check that `check_interval_seconds` has elapsed since target creation (default 300s = 5 min)

### "Frontend can't connect to API"

1. Ensure backend is running at `http://localhost:8000`
2. Check `VITE_API_BASE_URL` in `frontend/.env`
3. Check browser console (F12) for CORS errors or network failures

### "401 Unauthorized" errors

JWT token expired or invalid:
- Log out and log back in
- Check that `JWT_SECRET` is the same across sessions

## Project Structure

```
backend-api/
├── app/
│   ├── main.py           # FastAPI app
│   ├── config.py         # Settings from env
│   ├── database.py       # SQLAlchemy setup
│   ├── models.py         # DB models: User, Target, Check, Incident
│   ├── schemas.py        # Pydantic validation schemas
│   ├── auth.py           # JWT + password hashing
│   ├── dependencies.py   # get_current_user dependency
│   ├── routes_auth.py    # /auth/register, /auth/login
│   └── routes_targets.py # /targets CRUD + /check-now
├── main.py               # Entry point (python main.py)
├── test_main.py          # Pytest tests
├── requirements.txt      # Dependencies
└── .env.example          # Template

prober-worker/
├── config.py             # Settings from env
├── database.py           # SQLAlchemy + models
├── worker.py             # Main scheduler (python worker.py)
├── requirements.txt      # Dependencies
└── .env.example          # Template

frontend/
├── src/
│   ├── api.ts            # Axios client + interceptors
│   ├── types.ts          # TypeScript interfaces
│   ├── App.tsx           # Main component
│   ├── main.tsx          # Entry point
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   └── DashboardPage.tsx
│   └── components/
│       ├── TargetCard.tsx
│       ├── AddTargetForm.tsx
│       └── TargetDetailView.tsx
├── index.html
├── vite.config.ts
├── tailwind.config.ts
├── package.json
└── .env.example          # Template
```

## Next Steps

Now that Phase 1 is working locally, you can:

1. **Add more targets** to monitor
2. **Adjust check intervals** to see how the worker handles frequent checks
3. **Test failure scenarios** by pointing to broken URLs
4. **Run the test suite** to verify API behavior
5. **Explore the OpenAPI docs** at http://localhost:8000/docs

In **Phase 2**, this entire setup will be containerized and deployed to Kubernetes with Helm charts — but the application logic remains the same.

## Questions?

- Check logs in each service terminal for errors
- Review API docs at http://localhost:8000/docs
- Read the main [`README.md`](README.md) for vision and architecture

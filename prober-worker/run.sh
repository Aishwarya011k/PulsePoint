#!/bin/bash
# PulsePoint Phase 1 - Start Prober Worker
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🚀 Starting PulsePoint Prober Worker..."
echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Activate virtual environment
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run: python3 -m venv venv"
    exit 1
fi

source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import apscheduler" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Load environment
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Created .env - please verify DATABASE_URL matches backend"
fi

echo ""
echo "✅ All checks passed!"
echo "⏱️  Worker will check targets every 60 seconds"
echo "📊 Watch this terminal for check results"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the worker
python worker.py

#!/bin/bash
# PulsePoint Phase 1 - Start Frontend
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "🚀 Starting PulsePoint Frontend..."
echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Check if node_modules exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
fi

# Load environment
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "✅ Created .env"
fi

echo ""
echo "✅ All checks passed!"
echo "🌐 Starting dev server on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the dev server
npm run dev

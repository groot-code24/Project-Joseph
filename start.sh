#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [ ! -f .env ]; then
  echo "ERROR: Copy .env.example to .env and add your ANTHROPIC_API_KEY"
  exit 1
fi

set -a
# shellcheck disable=SC1091
. ./.env
set +a

if [ -z "${ANTHROPIC_API_KEY:-}" ] || [ "${ANTHROPIC_API_KEY}" = "sk-ant-your-key-here" ]; then
  echo "ERROR: ANTHROPIC_API_KEY in .env is missing or still the placeholder value."
  echo "       Edit .env and set ANTHROPIC_API_KEY=sk-ant-YOUR_REAL_KEY"
  exit 1
fi

if [ ! -d venv ]; then
  echo "Creating Python virtual environment at ./venv ..."
  python3 -m venv venv
fi
# shellcheck disable=SC1091
. venv/bin/activate

echo "Installing backend dependencies ..."
pip install -r backend/requirements.txt -q

echo "Initializing database ..."
python data/init_db.py

echo "Installing frontend dependencies ..."
npm install --prefix frontend --silent

BACK_PID=""
FRONT_PID=""

cleanup() {
  echo ""
  echo "Shutting down servers ..."
  [ -n "${BACK_PID}" ] && kill "${BACK_PID}" 2>/dev/null || true
  [ -n "${FRONT_PID}" ] && kill "${FRONT_PID}" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

( cd backend && exec uvicorn main:app --host 0.0.0.0 --port "${BACKEND_PORT:-8000}" --reload ) &
BACK_PID=$!

npm run dev --prefix frontend &
FRONT_PID=$!

echo ""
echo "✅ NovaMart Refund Agent is running!"
echo ""
echo "🌐 Frontend  →  http://localhost:${FRONTEND_PORT:-5173}"
echo "🔧 Backend   →  http://localhost:${BACKEND_PORT:-8000}"
echo "📋 API Docs  →  http://localhost:${BACKEND_PORT:-8000}/docs"
echo ""
echo "Press Ctrl+C to stop both servers."

wait

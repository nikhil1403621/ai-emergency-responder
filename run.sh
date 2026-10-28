#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "  AI-BASED EMERGENCY RESPONSE SYSTEM (ACADEMIC PROTOTYPE)  "
echo "=========================================================="

# Check Python 3
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install -r requirements.txt
fi

# Run pytest verification
echo "Running test suite..."
PYTHONPATH=backend ./venv/bin/pytest backend/tests/ -q

echo ""
echo "Starting FastAPI Application on http://localhost:8000 ..."
echo "API Docs available at: http://localhost:8000/docs"
echo "Web Interface available at: http://localhost:8000"
echo ""

PYTHONPATH=backend ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

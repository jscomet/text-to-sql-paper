#!/bin/bash
# Backend Start Script
# Usage: ./scripts/backend-start.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
PID_FILE="$BACKEND_DIR/.backend.pid"
PORT=8000

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if already running
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        log_warning "Backend is already running (PID: $pid)"
        log_info "API Docs: http://localhost:$PORT/docs"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# Check port
if command -v lsof >/dev/null 2>&1; then
    if lsof -i:$PORT >/dev/null 2>&1; then
        log_error "Port $PORT is already in use"
        exit 1
    fi
fi

cd "$BACKEND_DIR"

# Check virtual environment
if [ ! -d "venv" ]; then
    log_error "Virtual environment not found."
    log_info "Please run: cd backend && python -m venv venv"
    log_info "Then: source venv/Scripts/activate && pip install -r requirements.txt"
    exit 1
fi

log_info "Starting backend server..."

# Activate and start (without reload to ensure fresh code)
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
    uvicorn app.main:app --host 0.0.0.0 --port $PORT > backend.log 2>&1 &
else
    source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port $PORT > backend.log 2>&1 &
fi

pid=$!
echo $pid > "$PID_FILE"

sleep 2

if ps -p "$pid" > /dev/null 2>&1; then
    log_success "Backend started successfully!"
    log_info "API URL: http://localhost:$PORT"
    log_info "API Docs: http://localhost:$PORT/docs"
    log_info "Log: backend/backend.log"
else
    log_error "Backend failed to start. Check backend/backend.log"
    rm -f "$PID_FILE"
    exit 1
fi

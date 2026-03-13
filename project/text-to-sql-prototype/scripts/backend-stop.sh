#!/bin/bash
# Backend Stop Script
# Usage: ./scripts/backend-stop.sh

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

stopped=false

# Stop by PID file
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        kill "$pid" 2>/dev/null || true
        sleep 1
        if ps -p "$pid" > /dev/null 2>&1; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        log_success "Backend stopped (PID: $pid)"
        stopped=true
    fi
    rm -f "$PID_FILE"
fi

# Stop by port
if command -v lsof >/dev/null 2>&1; then
    pids=$(lsof -t -i:$PORT 2>/dev/null || true)
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9 2>/dev/null || true
        log_success "Backend stopped (Port: $PORT)"
        stopped=true
    fi
fi

# Stop uvicorn processes
if pgrep -f "uvicorn.*app.main:app" > /dev/null 2>&1; then
    pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
    log_success "Backend uvicorn processes stopped"
    stopped=true
fi

if [ "$stopped" = false ]; then
    log_warning "Backend was not running"
fi

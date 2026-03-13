#!/bin/bash
# Frontend Start Script
# Usage: ./scripts/frontend-start.sh

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
PID_FILE="$FRONTEND_DIR/.frontend.pid"
PORT=5173

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if already running
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        log_warning "Frontend is already running (PID: $pid)"
        log_info "Visit: http://localhost:$PORT"
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

cd "$FRONTEND_DIR"

# Install deps if needed
if [ ! -d "node_modules" ]; then
    log_warning "node_modules not found. Installing dependencies..."
    npm install
fi

log_info "Starting frontend dev server..."
npm run dev > frontend.log 2>&1 &
pid=$!
echo $pid > "$PID_FILE"

sleep 3

if ps -p "$pid" > /dev/null 2>&1; then
    log_success "Frontend started successfully!"
    log_info "App URL: http://localhost:$PORT"
    log_info "Log: frontend/frontend.log"
else
    log_error "Frontend failed to start. Check frontend/frontend.log"
    rm -f "$PID_FILE"
    exit 1
fi

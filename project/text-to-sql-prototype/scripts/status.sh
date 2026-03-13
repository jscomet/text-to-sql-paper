#!/bin/bash
# Text-to-SQL Prototype - Status Script
# Usage: ./scripts/status.sh

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# PID files
BACKEND_PID_FILE="$BACKEND_DIR/.backend.pid"
FRONTEND_PID_FILE="$FRONTEND_DIR/.frontend.pid"

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=5173

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_backend() {
    echo "Backend Service:"
    echo "  Port: $BACKEND_PORT"

    local pid_from_file=""
    local pid_from_port=""

    if [ -f "$BACKEND_PID_FILE" ]; then
        pid_from_file=$(cat "$BACKEND_PID_FILE")
        if ps -p "$pid_from_file" > /dev/null 2>&1; then
            log_success "  Status: RUNNING (PID: $pid_from_file)"
        else
            log_error "  Status: NOT RUNNING (stale PID file)"
            rm -f "$BACKEND_PID_FILE"
        fi
    else
        log_warning "  Status: NOT RUNNING"
    fi

    # Also check port
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i:$BACKEND_PORT > /dev/null 2>&1; then
            pid_from_port=$(lsof -t -i:$BACKEND_PORT)
            echo "  Port $BACKEND_PORT: OCCUPIED (PID: $pid_from_port)"
        else
            echo "  Port $BACKEND_PORT: FREE"
        fi
    fi

    echo "  Log: backend/backend.log"
    echo ""
}

check_frontend() {
    echo "Frontend Service:"
    echo "  Port: $FRONTEND_PORT"

    local pid_from_file=""
    local pid_from_port=""

    if [ -f "$FRONTEND_PID_FILE" ]; then
        pid_from_file=$(cat "$FRONTEND_PID_FILE")
        if ps -p "$pid_from_file" > /dev/null 2>&1; then
            log_success "  Status: RUNNING (PID: $pid_from_file)"
        else
            log_error "  Status: NOT RUNNING (stale PID file)"
            rm -f "$FRONTEND_PID_FILE"
        fi
    else
        log_warning "  Status: NOT RUNNING"
    fi

    # Also check port
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i:$FRONTEND_PORT > /dev/null 2>&1; then
            pid_from_port=$(lsof -t -i:$FRONTEND_PORT)
            echo "  Port $FRONTEND_PORT: OCCUPIED (PID: $pid_from_port)"
        else
            echo "  Port $FRONTEND_PORT: FREE"
        fi
    fi

    echo "  Log: frontend/frontend.log"
    echo ""
}

echo "=================================="
echo "Text-to-SQL Prototype - Status"
echo "=================================="
echo ""

check_backend
check_frontend

echo "Quick Commands:"
echo "  ./scripts/start.sh    # Start all services"
echo "  ./scripts/stop.sh     # Stop all services"
echo "  ./scripts/restart.sh  # Restart all services"

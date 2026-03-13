#!/bin/bash
# Text-to-SQL Prototype - Stop Script
# Usage: ./scripts/stop.sh [frontend|backend|all]

set -e

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

stop_backend() {
    log_info "Stopping backend server..."

    local stopped=false

    # Try to stop by PID file
    if [ -f "$BACKEND_PID_FILE" ]; then
        local pid=$(cat "$BACKEND_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" 2>/dev/null || true
            sleep 1
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null || true
            fi
            log_success "Backend stopped (PID: $pid)"
            stopped=true
        fi
        rm -f "$BACKEND_PID_FILE"
    fi

    # Also try to stop by port (in case started outside script)
    if command -v lsof >/dev/null 2>&1; then
        local pids=$(lsof -t -i:$BACKEND_PORT 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
            log_success "Backend stopped (Port: $BACKEND_PORT)"
            stopped=true
        fi
    fi

    # Try with pkill for uvicorn processes
    if pgrep -f "uvicorn.*app.main:app" > /dev/null 2>&1; then
        pkill -f "uvicorn.*app.main:app" 2>/dev/null || true
        log_success "Backend uvicorn processes stopped"
        stopped=true
    fi

    if [ "$stopped" = false ]; then
        log_warning "Backend was not running"
    fi
}

stop_frontend() {
    log_info "Stopping frontend dev server..."

    local stopped=false

    # Try to stop by PID file
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid" 2>/dev/null || true
            sleep 1
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null || true
            fi
            log_success "Frontend stopped (PID: $pid)"
            stopped=true
        fi
        rm -f "$FRONTEND_PID_FILE"
    fi

    # Also try to stop by port (in case started outside script)
    if command -v lsof >/dev/null 2>&1; then
        local pids=$(lsof -t -i:$FRONTEND_PORT 2>/dev/null || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -9 2>/dev/null || true
            log_success "Frontend stopped (Port: $FRONTEND_PORT)"
            stopped=true
        fi
    fi

    # Try with pkill for vite processes
    if pgrep -f "vite" > /dev/null 2>&1; then
        pkill -f "vite" 2>/dev/null || true
        log_success "Frontend vite processes stopped"
        stopped=true
    fi

    if [ "$stopped" = false ]; then
        log_warning "Frontend was not running"
    fi
}

show_help() {
    echo "Text-to-SQL Prototype - Stop Script"
    echo ""
    echo "Usage: $0 [frontend|backend|all]"
    echo ""
    echo "Commands:"
    echo "  backend   Stop only the backend server"
    echo "  frontend  Stop only the frontend dev server"
    echo "  all       Stop both backend and frontend (default)"
    echo "  help      Show this help message"
}

main() {
    local target="${1:-all}"

    case "$target" in
        backend)
            stop_backend
            ;;
        frontend)
            stop_frontend
            ;;
        all)
            stop_backend
            stop_frontend
            echo ""
            log_success "All services stopped!"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown command: $target"
            show_help
            exit 1
            ;;
    esac
}

main "$@"

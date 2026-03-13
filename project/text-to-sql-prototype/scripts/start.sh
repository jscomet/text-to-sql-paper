#!/bin/bash
# Text-to-SQL Prototype - Start Script
# Usage: ./scripts/start.sh [frontend|backend|all]

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

start_backend() {
    log_info "Starting backend server..."

    # Check if already running
    if [ -f "$BACKEND_PID_FILE" ]; then
        local pid=$(cat "$BACKEND_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_warning "Backend is already running (PID: $pid)"
            return 0
        else
            rm -f "$BACKEND_PID_FILE"
        fi
    fi

    # Check port availability
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i:$BACKEND_PORT >/dev/null 2>&1; then
            log_error "Port $BACKEND_PORT is already in use"
            return 1
        fi
    fi

    # Activate virtual environment and start backend
    cd "$BACKEND_DIR"

    if [ ! -d "venv" ]; then
        log_error "Virtual environment not found. Please run: cd backend && python -m venv venv"
        return 1
    fi

    # Start backend in background
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
        # Windows with Git Bash
        source venv/Scripts/activate
        uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > backend.log 2>&1 &
    else
        # Unix/Linux/Mac
        source venv/bin/activate
        nohup uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT --reload > backend.log 2>&1 &
    fi

    local backend_pid=$!
    echo $backend_pid > "$BACKEND_PID_FILE"

    # Wait for startup
    sleep 2

    if ps -p "$backend_pid" > /dev/null 2>&1; then
        log_success "Backend started successfully (PID: $backend_pid, Port: $BACKEND_PORT)"
        log_info "API Docs: http://localhost:$BACKEND_PORT/docs"
    else
        log_error "Backend failed to start. Check backend/backend.log"
        rm -f "$BACKEND_PID_FILE"
        return 1
    fi

    cd "$PROJECT_ROOT"
}

start_frontend() {
    log_info "Starting frontend dev server..."

    # Check if already running
    if [ -f "$FRONTEND_PID_FILE" ]; then
        local pid=$(cat "$FRONTEND_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_warning "Frontend is already running (PID: $pid)"
            return 0
        else
            rm -f "$FRONTEND_PID_FILE"
        fi
    fi

    # Check port availability
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i:$FRONTEND_PORT >/dev/null 2>&1; then
            log_error "Port $FRONTEND_PORT is already in use"
            return 1
        fi
    fi

    cd "$FRONTEND_DIR"

    if [ ! -d "node_modules" ]; then
        log_warning "node_modules not found. Installing dependencies..."
        npm install
    fi

    # Start frontend in background
    npm run dev > frontend.log 2>&1 &
    local frontend_pid=$!
    echo $frontend_pid > "$FRONTEND_PID_FILE"

    # Wait for startup
    sleep 3

    if ps -p "$frontend_pid" > /dev/null 2>&1; then
        log_success "Frontend started successfully (PID: $frontend_pid, Port: $FRONTEND_PORT)"
        log_info "App URL: http://localhost:$FRONTEND_PORT"
    else
        log_error "Frontend failed to start. Check frontend/frontend.log"
        rm -f "$FRONTEND_PID_FILE"
        return 1
    fi

    cd "$PROJECT_ROOT"
}

show_help() {
    echo "Text-to-SQL Prototype - Start Script"
    echo ""
    echo "Usage: $0 [frontend|backend|all]"
    echo ""
    echo "Commands:"
    echo "  backend   Start only the backend server"
    echo "  frontend  Start only the frontend dev server"
    echo "  all       Start both backend and frontend (default)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0           # Start both services"
    echo "  $0 backend   # Start only backend"
    echo "  $0 frontend  # Start only frontend"
}

main() {
    local target="${1:-all}"

    case "$target" in
        backend)
            start_backend
            ;;
        frontend)
            start_frontend
            ;;
        all)
            start_backend
            echo ""
            start_frontend
            echo ""
            log_success "All services started!"
            echo ""
            echo "  Frontend: http://localhost:$FRONTEND_PORT"
            echo "  Backend:  http://localhost:$BACKEND_PORT"
            echo "  API Docs: http://localhost:$BACKEND_PORT/docs"
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

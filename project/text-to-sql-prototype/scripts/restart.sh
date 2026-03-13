#!/bin/bash
# Text-to-SQL Prototype - Restart Script
# Usage: ./scripts/restart.sh [frontend|backend|all]

set -e

# Colors for output
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project directories
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

show_help() {
    echo "Text-to-SQL Prototype - Restart Script"
    echo ""
    echo "Usage: $0 [frontend|backend|all]"
    echo ""
    echo "Commands:"
    echo "  backend   Restart only the backend server"
    echo "  frontend  Restart only the frontend dev server"
    echo "  all       Restart both backend and frontend (default)"
    echo "  help      Show this help message"
}

main() {
    local target="${1:-all}"

    case "$target" in
        backend|frontend|all)
            log_info "Restarting $target service(s)..."
            echo ""

            # Stop
            "$PROJECT_ROOT/scripts/stop.sh" "$target"
            echo ""

            # Wait a moment
            sleep 1

            # Start
            "$PROJECT_ROOT/scripts/start.sh" "$target"
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "Unknown command: $target"
            show_help
            exit 1
            ;;
    esac
}

main "$@"

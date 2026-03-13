#!/bin/bash
# Frontend Restart Script
# Usage: ./scripts/frontend-restart.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Restarting frontend..."
"$PROJECT_ROOT/scripts/frontend-stop.sh"
echo ""
sleep 1
"$PROJECT_ROOT/scripts/frontend-start.sh"

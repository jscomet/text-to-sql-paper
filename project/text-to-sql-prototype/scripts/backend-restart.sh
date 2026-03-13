#!/bin/bash
# Backend Restart Script
# Usage: ./scripts/backend-restart.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Restarting backend..."
"$PROJECT_ROOT/scripts/backend-stop.sh"
echo ""
sleep 1
"$PROJECT_ROOT/scripts/backend-start.sh"

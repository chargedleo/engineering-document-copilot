#!/usr/bin/env bash
# Shell Development Setup Script
set -e

echo "=== Setting up Engineering Document Intelligence & CAD Copilot ==="

# 1. Environment file check
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
else
    echo ".env already exists."
fi

# 2. Python check & venv creation
if command -v python3 &>/dev/null; then
    echo "Found Python: $(python3 --version)"
    if [ ! -d "backend/.venv" ]; then
        echo "Creating backend virtual environment..."
        python3 -m venv backend/.venv
        echo "To activate: source backend/.venv/bin/activate"
    fi
else
    echo "Warning: python3 not found. Please install Python 3.11+."
fi

# 3. Node.js check
if command -v node &>/dev/null; then
    echo "Found Node: $(node --version)"
else
    echo "Warning: Node.js not found. Please install Node.js 18+."
fi

echo "=== Setup check complete! ==="

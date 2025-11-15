#!/bin/bash

echo "=========================================="
echo "Installing Context Edge - Edge Device SDK"
echo "=========================================="

# Check if python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not installed"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Install the package in editable mode
echo "Installing Edge SDK in editable mode..."
pip install -e .

echo ""
echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "To use the SDK:"
echo "  source venv/bin/activate"
echo ""
echo "To test:"
echo "  python3 test_cim.py"
echo ""

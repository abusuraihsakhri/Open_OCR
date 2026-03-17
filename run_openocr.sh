#!/bin/bash

echo "=========================================="
echo "      OpenOCR - One-Click Launcher        "
echo "=========================================="
echo "Developed by Dr. Abu Suraih Sakhri"
echo ""

# 1. Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] python3 could not be found. Please install it."
    exit 1
fi

# 2. Check for virtual environment
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install dependencies
echo "[INFO] Checking dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Launch Application
echo "[SUCCESS] Starting OpenOCR..."
python3 src/main.py

# Keep terminal open on error
if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Application crashed."
    read -p "Press enter to exit..."
fi

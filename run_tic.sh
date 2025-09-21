#!/bin/bash
# TIC System Quick Launcher

echo "🚀 TIC System Launcher"
echo "====================="

# Check if virtual environment exists
if [ ! -d "ticvenv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please ensure you're in the TIC directory with ticvenv/"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source ticvenv/bin/activate

# Check if in correct directory
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found!"
    echo "Please run this script from the TIC directory"
    exit 1
fi

echo "🎯 Starting TIC System..."
echo ""

# Run the main script with any passed arguments
python main.py "$@"

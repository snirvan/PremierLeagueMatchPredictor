#!/bin/bash

# Premier League Data Update Script
# This script activates the virtual environment and runs the data updater

echo "🚀 Starting Premier League Data Update..."
echo "🔧 Activating virtual environment..."

# Activate virtual environment
source venv/bin/activate

# Check if required packages are installed
echo "📋 Checking dependencies..."
python -c "import requests, pandas, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Installing required packages..."
    pip install -r scraper_requirements.txt
fi

# Run the updater
echo "📥 Running data updater..."
python update_matches_scraper.py

echo "✅ Update process completed!"
echo "💡 Check the output above to see how many matches were added."

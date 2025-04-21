#!/bin/bash

# This script runs tests for the Google Forms Multi-Language Tool

echo "Running tests for Google Forms Multi-Language Tool..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if required modules are installed
echo "Checking required modules..."
python3 -c "import flask, google.oauth2, google_auth_oauthlib, googleapiclient, pandas, matplotlib, seaborn, reportlab, googletrans, pdfkit" || {
    echo "Error: Some required modules are missing. Please run 'pip install -r requirements.txt'"
    exit 1
}

# Check if required files exist
echo "Checking required files..."
required_files=(
    "app.py"
    "auth.py"
    "forms.py"
    "translation.py"
    "aggregation.py"
    "visualization.py"
    "report.py"
    "sharing.py"
    "config.py"
    "templates/index.html"
    "templates/dashboard.html"
    "templates/results.html"
    "templates/about.html"
    "templates/shared_expired.html"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "Error: Required file $file not found."
        exit 1
    fi
done

# Check if required directories exist
echo "Checking required directories..."
required_dirs=(
    "static"
    "templates"
)

for dir in "${required_dirs[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "Error: Required directory $dir not found."
        exit 1
    fi
done

# Create test directories if they don't exist
echo "Creating test directories..."
mkdir -p static/img
mkdir -p static/reports
mkdir -p static/data
mkdir -p static/packages
mkdir -p static/shares

# Run a basic syntax check on Python files
echo "Running syntax check on Python files..."
python_files=(
    "app.py"
    "auth.py"
    "forms.py"
    "translation.py"
    "aggregation.py"
    "visualization.py"
    "report.py"
    "sharing.py"
    "config.py"
)

for file in "${python_files[@]}"; do
    python3 -m py_compile "$file" || {
        echo "Error: Syntax error in $file"
        exit 1
    }
done

echo "All tests passed! The application is ready to run."
echo "To start the application, run: python app.py"
echo "Then access the web interface at http://localhost:5000"

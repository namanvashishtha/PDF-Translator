#!/bin/bash

echo "Deploying PDF Translator..."

# Remove existing virtual environment
if [ -d "venv" ]; then
    rm -rf venv
fi

# Create new virtual environment
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "Failed to create virtual environment"
    exit 1
fi

# Upgrade pip
venv/bin/python -m pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo "Failed to upgrade pip"
    exit 1
fi

# Install dependencies
venv/bin/pip install --no-cache-dir -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to install dependencies"
    exit 1
fi

echo ""
echo "✓ Deployment completed successfully!"
echo "Your PDF Translator is ready to use!"
echo ""
echo "To activate the environment, run: source venv/bin/activate"
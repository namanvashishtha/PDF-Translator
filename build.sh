#!/bin/bash

echo "Building PDF Translator for Railway..."

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Create Python virtual environment
echo "Creating Python virtual environment..."
python3 -m venv venv

# Activate virtual environment and install Python dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Build the frontend
echo "Building frontend..."
npm run build

echo "Build completed successfully!"
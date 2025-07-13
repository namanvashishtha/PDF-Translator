#!/bin/bash

echo "Building PDF Translator for Railway..."

# Ensure we don't use uv
export UV_NO_SYNC=1
unset UV_CACHE_DIR

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

# Create Python virtual environment using traditional method
echo "Creating Python virtual environment..."
python3.11 -m venv venv

# Activate virtual environment and install Python dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Verify Python dependencies
echo "Verifying Python dependencies..."
python -c "import deep_translator, langdetect, pymupdf, reportlab, wand; print('✓ All Python dependencies installed successfully')"

# Build the frontend
echo "Building frontend..."
npm run build

echo "Build completed successfully!"
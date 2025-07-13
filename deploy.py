#!/usr/bin/env python3
"""
Deployment script for PDF Translator
Sets up environment and installs only production dependencies
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed:")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def main():
    """Main deployment function"""
    print("Deploying PDF Translator...")
    
    # Create virtual environment
    run_command("python -m venv venv", "Creating virtual environment")
    
    # Determine pip path based on OS
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        pip_cmd = "venv/bin/pip"
    
    # Install dependencies
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        python_cmd = "venv/bin/python"
    
    run_command(f"{python_cmd} -m pip install --upgrade pip", "Upgrading pip")
    run_command(f"{pip_cmd} install --no-cache-dir -r requirements.txt", "Installing production dependencies")
    
    print("\n✓ Deployment completed successfully!")
    print("Your PDF Translator is ready to use!")

if __name__ == "__main__":
    main()
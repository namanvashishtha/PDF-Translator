#!/usr/bin/env python3
"""
Setup script for PDF Translator
Creates virtual environment and installs dependencies
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
        return None

def main():
    """Main setup function"""
    print("Setting up PDF Translator environment...")
    
    # Create virtual environment
    if not os.path.exists("venv"):
        run_command("python -m venv venv", "Creating virtual environment")
    else:
        print("✓ Virtual environment already exists")
    
    # Activate and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Install dependencies
    run_command(f"{python_cmd} -m pip install --upgrade pip", "Upgrading pip")
    run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies")
    
    print("\n✓ Setup completed successfully!")
    print(f"To activate the environment, run: {activate_cmd}")

if __name__ == "__main__":
    main()
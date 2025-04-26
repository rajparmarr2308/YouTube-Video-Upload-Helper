#!/usr/bin/env python
"""
Setup script for YouTube Video Upload Helper.
This script checks dependencies and sets up the environment.
"""
import os
import sys
import subprocess
import shutil

def check_python_version():
    """Check Python version is 3.7+"""
    if sys.version_info < (3, 7):
        print("ERROR: Python 3.7 or higher is required.")
        sys.exit(1)
    print("✓ Python version check passed")

def install_dependencies():
    """Install dependencies from requirements.txt"""
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("ERROR: Failed to install dependencies.")
        sys.exit(1)

def setup_env_file():
    """Setup .env file if it doesn't exist"""
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✓ Created .env file from example. Please update it with your API keys.")
        else:
            print("WARNING: .env.example file not found, couldn't create .env file.")

def create_directories():
    """Create necessary directories"""
    directories = ["uploads"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    print("✓ Created necessary directories")

def main():
    """Main setup function"""
    print("Setting up YouTube Video Upload Helper...")
    
    check_python_version()
    install_dependencies()
    setup_env_file()
    create_directories()
    
    print("\nSetup complete! 🎉")
    print("\nTo run the application:")
    print("1. Edit the .env file to add your API keys")
    print("2. Run 'python app.py'")
    print("3. Open your browser to http://localhost:5000")

if __name__ == "__main__":
    main() 
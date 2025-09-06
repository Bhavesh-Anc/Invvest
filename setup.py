#!/usr/bin/env python3
"""
AI Stock Advisor Pro - Setup Script
Automated installation and setup
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ required")
        print(f"   Current: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def install_requirements():
    """Install required packages"""
    try:
        print("📦 Installing requirements...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print("✅ Requirements installed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        return False

def setup_directories():
    """Create necessary directories"""
    dirs = ['data', 'logs', 'models', 'cache', 'reports']
    for directory in dirs:
        Path(directory).mkdir(exist_ok=True)
    print("✅ Directories created")

def setup_config():
    """Set up configuration"""
    config_dir = Path("config")
    secrets_file = config_dir / "secrets.py"
    template_file = config_dir / "secrets_template.py"

    if not secrets_file.exists() and template_file.exists():
        import shutil
        shutil.copy(template_file, secrets_file)
        print("📝 Configuration template copied")
        print("   Edit config/secrets.py with your API keys")
    else:
        print("✅ Configuration ready")

def main():
    """Main setup function"""
    print("🚀 AI Stock Advisor Pro - Setup")
    print("=" * 40)

    if not check_python_version():
        sys.exit(1)

    setup_directories()

    if not install_requirements():
        sys.exit(1)

    setup_config()

    print("\n" + "=" * 40)
    print("✅ Setup completed!")
    print("\n📋 Next steps:")
    print("   1. Edit config/secrets.py (optional)")
    print("   2. Run: streamlit run app.py")
    print("   3. Open: http://localhost:8501")
    print("\n🎉 Ready to trade smartly!")

if __name__ == "__main__":
    main()

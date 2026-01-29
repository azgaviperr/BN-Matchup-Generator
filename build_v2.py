# build.py V2
"""
Build script for BN Matchup Generator V2.
Packages the V2 application into standalone executables.

Usage:
    python build_v2.py
"""
import os
import sys
import subprocess
import platform

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = "dist_v2"

def build_executable():
    """Build executable for current platform."""
    current_os = platform.system().lower()
    
    print(f"== Building BN Matchup Generator V2 for {current_os} ==")
    
    # Create dist directory
    os.makedirs(DIST_DIR, exist_ok=True)
    
    # Prepare PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--distpath", DIST_DIR,
        "--workpath", "build_v2",
        "--specpath", "build_v2",
        "--clean",
        "--onefile",
        "--name", "matchup_generator_v2",
    ]
    
    # Add windowed option for GUI on Windows
    if current_os.startswith("win"):
        cmd.append("--windowed")
    
    # Add the main script
    cmd.append("matchup_generator_v2.py")
    
    print(f"Running: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✓ Build successful! Executable in '{DIST_DIR}/' directory")
    except subprocess.CalledProcessError as e:
        print(f"\n✗ Build failed: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("\n✗ PyInstaller not found. Install with: pip install pyinstaller")
        sys.exit(1)

if __name__ == "__main__":
    build_executable()

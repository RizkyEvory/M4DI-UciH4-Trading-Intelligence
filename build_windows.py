"""
M4DI~UciH4 Trading Intelligence System
Windows PyInstaller Standalone Build Script
Automates packaging into a standalone Windows .exe application.
"""
import subprocess
import sys
import shutil
from pathlib import Path


def build():
    print("====================================================================")
    print("  👑 M4DI~UciH4 Trading Intelligence — Windows Packager")
    print("====================================================================")

    # Check PyInstaller availability
    try:
        import PyInstaller
        print(f"[✓] PyInstaller detected: version {PyInstaller.__version__}")
    except ImportError:
        print("[!] PyInstaller is not installed.")
        print("[*] Installing PyInstaller via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    # Target spec file
    spec_path = Path("m4di_ucih4.spec")
    if not spec_path.exists():
        print(f"[X] Spec file '{spec_path}' not found!")
        sys.exit(1)

    print("[*] Starting PyInstaller build process...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        str(spec_path)
    ]

    result = subprocess.run(cmd)
    if result.returncode == 0:
        dist_dir = Path("dist") / "M4DI_UciH4_Trading_Intelligence"
        exe_file = dist_dir / "M4DI_UciH4_Trading_Intelligence.exe"
        print("====================================================================")
        print("  🎉 Windows Executable Build SUCCESSFUL!")
        print(f"  📁 Output Directory: {dist_dir.resolve()}")
        print(f"  🚀 Executable:       {exe_file.resolve()}")
        print("====================================================================")
    else:
        print(f"[X] Build failed with exit code: {result.returncode}")
        sys.exit(result.returncode)


if __name__ == "__main__":
    build()

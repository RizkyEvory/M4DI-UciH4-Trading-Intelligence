# 📦 M4DI~UciH4 Trading Intelligence System — Installation Guide

## System Requirements

- **Operating System**: Windows 10 / 11 (64-bit), Linux (Ubuntu 20.04+, Debian 11+, Arch), or macOS 12+
- **Python Version**: Python 3.11, 3.12, 3.13, or 3.14+
- **Hardware Minimum**: 4 GB RAM, 500 MB free disk space, 1280x720 display resolution
- **Hardware Recommended**: 8 GB+ RAM, 1080p Full HD display

---

## 🚀 Standard Installation (Source Code)

### Step 1: Clone or Extract Repository

Ensure the application folder is placed in your desired workspace, for example:
```powershell
cd "c:\Users\qwert\PROJECT APLIKASI"
```

### Step 2: Create a Virtual Environment (Optional but Recommended)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies

Install the core security, networking, and imaging dependencies:
```powershell
pip install -r requirements.txt
```

Verified dependencies:
- `cryptography>=41.0.0` (Local PBKDF2 credential encryption)
- `requests>=2.28.0` (HTTPS communication for Finnhub, Twelve Data, NewsAPI, and Telegram)
- `Pillow>=10.0.0` (Image handling and icon rendering)

### Step 4: Run the Application

Launch the desktop interface directly:
```powershell
python main.py
```

---

## 🪟 Building a Standalone Windows Executable (.exe)

You can package the application into a standalone Windows desktop binary without needing Python installed on target machines:

1. Install PyInstaller:
   ```powershell
   pip install pyinstaller
   ```
2. Run the automated build script:
   ```powershell
   python build_windows.py
   ```
3. Locate the compiled executable inside:
   `dist\M4DI_UciH4_Trading_Intelligence\M4DI_UciH4_Trading_Intelligence.exe`

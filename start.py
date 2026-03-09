#!/usr/bin/env python3
"""
ICP Identifier — One-click launcher
Usage: python start.py
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

ROOT = Path(__file__).parent
VENV = ROOT / ".venv"
PORT = 8501
URL = f"http://localhost:{PORT}"

# Colors
G = "\033[92m"  # green
B = "\033[94m"  # blue
Y = "\033[93m"  # yellow
R = "\033[91m"  # red
W = "\033[0m"   # reset
BOLD = "\033[1m"


def pip():
    return str(VENV / "bin" / "pip")


def python():
    return str(VENV / "bin" / "python")


def streamlit():
    return str(VENV / "bin" / "streamlit")


def step(msg):
    print(f"\n{B}{'─' * 50}{W}")
    print(f"  {BOLD}{msg}{W}")
    print(f"{B}{'─' * 50}{W}")


def check_python():
    """Ensure Python 3.10-3.13 is available."""
    v = sys.version_info
    if v.major == 3 and 10 <= v.minor <= 13:
        return sys.executable

    # Try python3.12 explicitly
    for cmd in ["python3.12", "python3.11", "python3.10", "python3.13"]:
        try:
            result = subprocess.run([cmd, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                return cmd
        except FileNotFoundError:
            continue

    print(f"{R}Python 3.10-3.13 required. Current: {v.major}.{v.minor}{W}")
    print(f"{Y}Install with: brew install python@3.12{W}")
    sys.exit(1)


def setup_venv(py):
    """Create virtual environment if needed."""
    if (VENV / "bin" / "activate").exists():
        return

    step("Creating virtual environment...")
    subprocess.run([py, "-m", "venv", str(VENV)], check=True)
    print(f"  {G}venv created{W}")


def install_deps():
    """Install dependencies if needed."""
    try:
        result = subprocess.run(
            [python(), "-c", "import streamlit; import plotly; import openai"],
            capture_output=True,
        )
        if result.returncode == 0:
            return
    except Exception:
        pass

    step("Installing dependencies...")
    subprocess.run(
        [pip(), "install", "-r", str(ROOT / "requirements.txt"), "-q"],
        check=True,
    )
    print(f"  {G}Dependencies installed{W}")


def check_env():
    """Check if .env file has API key."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        step("Setting up environment...")
        print(f"  {Y}No .env file found.{W}")
        key = input(f"  Enter your GROQ API key (or press Enter to skip): ").strip()
        if key:
            env_file.write_text(f"GROQ_API_KEY={key}\n")
            print(f"  {G}API key saved to .env{W}")
        else:
            env_file.write_text("GROQ_API_KEY=\n")
            print(f"  {Y}Skipped. Pre-loaded companies will work without API key.{W}")
    else:
        content = env_file.read_text()
        has_key = any(
            line.startswith("GROQ_API_KEY=") and len(line.split("=", 1)[1].strip()) > 5
            for line in content.splitlines()
        )
        if not has_key:
            print(f"  {Y}Warning: GROQ_API_KEY is empty. Research features need it.{W}")


def kill_existing():
    """Kill any existing streamlit on same port."""
    subprocess.run(
        ["lsof", "-ti", f":{PORT}"],
        capture_output=True,
    )
    result = subprocess.run(
        ["lsof", "-ti", f":{PORT}"],
        capture_output=True, text=True,
    )
    if result.stdout.strip():
        for pid in result.stdout.strip().split("\n"):
            try:
                os.kill(int(pid), 9)
            except (ValueError, ProcessLookupError):
                pass
        time.sleep(1)


def launch():
    """Launch streamlit and open browser."""
    step("Starting ICP Identifier...")

    kill_existing()

    print(f"""
  {BOLD}{G}ICP Identifier{W}
  {B}URL:{W}  {URL}

  {Y}Press Ctrl+C to stop{W}
""")

    # Open browser after a short delay
    def open_browser():
        time.sleep(2)
        webbrowser.open(URL)

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Run streamlit (blocking)
    os.execv(
        streamlit(),
        [
            streamlit(),
            "run", str(ROOT / "app.py"),
            f"--server.port={PORT}",
            "--server.headless=true",
            "--browser.gatherUsageStats=false",
        ],
    )


def main():
    print(f"""
{B}╔══════════════════════════════════════╗
║  {BOLD}{G}ICP Identifier{W}{B}                      ║
║  {W}by Bruno Seixas{B}                      ║
╚══════════════════════════════════════╝{W}""")

    py = check_python()
    setup_venv(py)
    install_deps()
    check_env()
    launch()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Y}Stopped.{W}")

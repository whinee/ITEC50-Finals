import asyncio
import os
import sys

from hypercorn.asyncio import serve
from hypercorn.config import Config


def get_base_path():
    """
    Get the absolute path to the bundled resources.
    PyInstaller creates a temporary folder and stores its path in sys._MEIPASS.
    If we're not running as a PyInstaller bundle, this falls back to the current working directory.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


async def run_server():
    from main import app  # Import app here to ensure environment variables and paths are set first

    config = Config()
    config.bind = ["127.0.0.1:8080"]  # Bind to localhost on port 8080 by default
    config.use_reloader = False       # Reloading is incompatible with PyInstaller binaries
    
    print(f"DeciMark Offline Edition Starting on http://127.0.0.1:8080")
    print(f"Base Path: {get_base_path()}")
    
    await serve(app, config)


if __name__ == "__main__":
    # Force the current working directory to the bundled base path so that relative paths (like reading .env or templates) work properly.
    base_path = get_base_path()
    os.chdir(base_path)
    
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        print("\nShutting down DeciMark...")
    except Exception as e:
        print(f"Fatal error starting server: {e}")
        input("Press Enter to exit...")  # Pause before closing terminal window on Windows

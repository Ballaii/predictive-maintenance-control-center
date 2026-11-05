"""Container entrypoint: bind the runtime-provided port without shell interpolation."""
import logging
import os
import subprocess
import sys


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    port = int(os.environ.get("PORT", "8080"))
    if not 1 <= port <= 65535:
        raise ValueError("PORT must be between 1 and 65535.")
    logging.info("Starting dashboard on 0.0.0.0:%s; no training or cloud setup at startup", port)
    raise SystemExit(subprocess.call([
        sys.executable, "-m", "streamlit", "run", "app.py",
        "--server.address=0.0.0.0", f"--server.port={port}", "--server.headless=true",
    ]))


if __name__ == "__main__":
    main()

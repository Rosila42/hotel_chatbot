from __future__ import annotations

import os
import threading
import time
import webbrowser

import uvicorn

import main


HOST = os.environ.get("CHATBOT_HOST", "127.0.0.1")
PORT = int(os.environ.get("CHATBOT_PORT", "8000"))
URL = f"http://{HOST}:{PORT}/app/"


def open_browser() -> None:
    time.sleep(1.0)
    webbrowser.open(URL)


def main_entry() -> None:
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(main.app, host=HOST, port=PORT, log_level="info")


if __name__ == "__main__":
    main_entry()

# Vibe coded: this web interface was written with an AI assistant in 2026.
"""Start the web interface: python -m web_app"""
import os

import uvicorn

if __name__ == "__main__":
    port = int(os.getenv("WEB_PORT", "8000"))
    print(f"Customer shop: http://127.0.0.1:{port}/    Staff: http://127.0.0.1:{port}/staff")
    uvicorn.run("web_app.server:app", host="127.0.0.1", port=port, log_level="warning")

"""Run the API on AEGIS_PORT: ``python -m app`` (from backend/)."""

import uvicorn

from .config import get_settings

if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host="127.0.0.1", port=get_settings().port)

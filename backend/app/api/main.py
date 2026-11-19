"""FastAPI application: lifespan wiring of hub + USB monitor, CORS, routes."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings
from ..core.usb_monitor import UsbMonitor
from .routes import router
from .ws_manager import Hub


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start the hub and monitor on startup; stop and cancel scans on shutdown."""
    logging.basicConfig(
        level=logging.INFO,
        format="ts=%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s",
    )
    settings = get_settings()
    hub = Hub()
    hub.start(asyncio.get_running_loop())
    monitor = UsbMonitor(hub)
    app.state.hub, app.state.monitor, app.state.intel_online = hub, monitor, []
    if settings.watch_usb:
        monitor.start()
    try:
        yield
    finally:
        monitor.stop()
        await hub.stop()


app = FastAPI(title="AEGIS USB", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

"""FastAPI application: lifespan wiring of hub, USB monitor, intel, audit, keys and vault."""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import Settings, get_settings
from ..core.usb_monitor import UsbMonitor
from ..core.vault import Vault
from ..crypto.audit_chain import AuditChain
from ..crypto.keystore import KeyStore
from ..engine.intel.service import IntelService
from .routes import router
from .ws_manager import Hub

log = logging.getLogger("aegis.api")


def resolve_hmac_secret(settings: Settings) -> str:
    """Use AEGIS_HMAC_SECRET; if unset, create and persist a random one (mode 0600)."""
    if settings.hmac_secret:
        return settings.hmac_secret
    path: Path = settings.data_dir / "hmac.secret"
    if path.exists():
        return path.read_text().strip()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    value = secrets.token_hex(32)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(value)
    log.warning("AEGIS_HMAC_SECRET not set: generated one in %s", path)
    return value


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start everything on startup; stop and cancel scans on shutdown."""
    logging.basicConfig(
        level=logging.INFO,
        format="ts=%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s",
    )
    settings = get_settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    audit = AuditChain(settings.data_dir / "audit.db", resolve_hmac_secret(settings))
    hub = Hub(audit)
    hub.start(asyncio.get_running_loop())
    intel = IntelService(settings, audit=audit)
    hub.file_hooks.append(intel.submit)
    intel.start(hub.publish)
    monitor = UsbMonitor(hub)
    app.state.hub, app.state.monitor, app.state.audit = hub, monitor, audit
    app.state.intel = intel
    app.state.keystore = KeyStore(settings.data_dir / "keys")
    app.state.vault = Vault(settings.data_dir / "vault", settings.vault_passphrase)
    if settings.watch_usb:
        monitor.start()
    try:
        yield
    finally:
        monitor.stop()
        await intel.stop()
        await hub.stop()
        audit.close()


app = FastAPI(title="AEGIS USB", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

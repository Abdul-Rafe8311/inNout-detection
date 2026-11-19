"""REST endpoints (§7.3)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request, WebSocket

from ..config import get_settings
from ..core.usb_monitor import DriveInfo
from ..engine import yara_scanner
from .schemas import EjectResponse, HealthResponse, SimulateResponse, Stats
from .ws_manager import serve_client

router = APIRouter()
SIM_DRIVE = "Z:\\"


def _require_demo() -> None:
    if not get_settings().demo_mode:
        raise HTTPException(403, "Demo endpoints are disabled (AEGIS_DEMO_MODE=false)")


@router.get("/api/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Liveness plus YARA rule count, intel providers online and WS client count."""
    state = request.app.state
    return HealthResponse(
        status="ok",
        yara_rules=yara_scanner.rule_count(),
        intel_providers_online=list(getattr(state, "intel_online", [])),
        ws_clients=state.hub.client_count,
    )


@router.get("/api/stats", response_model=Stats)
async def stats(request: Request) -> Stats:
    """Cumulative tier counters for this server session."""
    return request.app.state.hub.stats


@router.get("/api/history")
async def history(request: Request, limit: int = Query(500, ge=1, le=500)) -> list[dict]:
    """Most recent events (oldest first), same data as the WebSocket SNAPSHOT."""
    return list(request.app.state.hub.history)[-limit:]


@router.post("/api/demo/simulate", response_model=SimulateResponse)
async def simulate(request: Request) -> SimulateResponse:
    """Scan the demo folder as virtual drive Z:\\ (no real USB needed)."""
    _require_demo()
    root = get_settings().demo_drive_path
    if not root.is_dir():
        raise HTTPException(
            409, "Demo drive missing. Run: python qa_demo/generate_payloads.py"
        )
    monitor = request.app.state.monitor
    existing = monitor.job(SIM_DRIVE)
    if existing is not None:
        if existing.is_alive():
            raise HTTPException(409, "Simulated drive is already being scanned")
        monitor.eject(SIM_DRIVE)
    info = DriveInfo(SIM_DRIVE, "AEGIS_DEMO", "simulated", 0, simulated=True)
    job = monitor.start_scan(str(root), info)
    return SimulateResponse(scan_id=job.scan_id, drive=SIM_DRIVE)


@router.post("/api/demo/eject", response_model=EjectResponse)
async def eject(request: Request, drive: str = SIM_DRIVE) -> EjectResponse:
    """Remove the simulated drive, cancelling any scan in progress."""
    _require_demo()
    return EjectResponse(ejected=request.app.state.monitor.eject(drive))


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket) -> None:
    """Live telemetry: SNAPSHOT first, then events."""
    await serve_client(ws, ws.app.state.hub)

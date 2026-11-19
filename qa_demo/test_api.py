"""API, WebSocket and schema-contract tests (§10)."""

import re
from pathlib import Path

import pytest
from app.api import schemas
from app.config import get_settings
from fastapi.testclient import TestClient

import generate_payloads as gp

TELEMETRY_TS = Path(__file__).resolve().parents[1] / "frontend/src/types/telemetry.ts"


@pytest.fixture()
def client(drive, monkeypatch):
    monkeypatch.setenv("AEGIS_DEMO_DRIVE_PATH", str(drive))
    monkeypatch.setenv("AEGIS_WATCH_USB", "false")
    monkeypatch.setenv("AEGIS_DEMO_MODE", "true")
    get_settings.cache_clear()
    from app.api.main import app

    with TestClient(app) as c:
        yield c
    get_settings.cache_clear()


def collect_until_complete(ws, limit=200):
    events = []
    for _ in range(limit):
        ev = ws.receive_json()
        events.append(ev)
        if ev["type"] == "SCAN_COMPLETE":
            return events
    raise AssertionError("no SCAN_COMPLETE")


def test_health_and_empty_state(client):
    h = client.get("/api/health").json()
    assert h["status"] == "ok" and h["yara_rules"] == 6 and h["ws_clients"] == 0
    assert client.get("/api/stats").json()["total"] == 0
    assert client.get("/api/history").json() == []


def test_websocket_snapshot_first_then_simulate(client):
    n = len(gp.EXPECTED)
    with client.websocket_connect("/ws") as ws:
        first = ws.receive_json()
        assert first["type"] == "SNAPSHOT" and first["events"] == []
        assert client.post("/api/demo/simulate").status_code == 200
        events = collect_until_complete(ws)
    types = [e["type"] for e in events]
    assert types[0] == "USB_CONNECTED"
    assert types.count("FILE_SCANNED") == n
    done = events[-1]
    assert done["total"] == n and (done["safe"], done["suspicious"], done["critical"]) == (3, 2, 7)
    ids = [e["event_id"] for e in events]
    assert len(ids) == len(set(ids))
    tiers = {e["filename"]: e["tier"] for e in events if e["type"] == "FILE_SCANNED"}
    for rel, (tier, _) in gp.EXPECTED.items():
        assert tiers[Path(rel).name] == tier


def test_reconnect_snapshot_repopulates_without_duplicates(client):
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        client.post("/api/demo/simulate")
        collect_until_complete(ws)
    with client.websocket_connect("/ws") as ws:
        snap = ws.receive_json()
    assert snap["type"] == "SNAPSHOT"
    ids = [e["event_id"] for e in snap["events"]]
    assert len(ids) == len(set(ids))
    assert sum(e["type"] == "FILE_SCANNED" for e in snap["events"]) == len(gp.EXPECTED)
    assert snap["stats"]["total"] == len(gp.EXPECTED)
    assert snap["drives"][0]["drive"] == "Z:\\" and snap["drives"][0]["scanning"] is False
    assert client.get("/api/stats").json()["critical"] == 7
    assert len(client.get("/api/history?limit=5").json()) == 5


def test_eject_and_resimulate(client):
    with client.websocket_connect("/ws") as ws:
        ws.receive_json()
        client.post("/api/demo/simulate")
        collect_until_complete(ws)
        assert client.post("/api/demo/eject").json() == {"ejected": True}
        while (ev := ws.receive_json())["type"] != "USB_DISCONNECTED":
            pass
        assert client.post("/api/demo/eject").json() == {"ejected": False}
        assert client.post("/api/demo/simulate").status_code == 200
        collect_until_complete(ws)


def test_simulate_without_drive_is_409(drive, monkeypatch, tmp_path):
    monkeypatch.setenv("AEGIS_DEMO_DRIVE_PATH", str(tmp_path / "nope"))
    monkeypatch.setenv("AEGIS_WATCH_USB", "false")
    get_settings.cache_clear()
    from app.api.main import app

    with TestClient(app) as c:
        assert c.post("/api/demo/simulate").status_code == 409
    get_settings.cache_clear()


def test_demo_mode_off_blocks_demo_endpoints(drive, monkeypatch):
    monkeypatch.setenv("AEGIS_DEMO_MODE", "false")
    monkeypatch.setenv("AEGIS_WATCH_USB", "false")
    get_settings.cache_clear()
    from app.api.main import app

    with TestClient(app) as c:
        assert c.post("/api/demo/simulate").status_code == 403
        assert c.post("/api/demo/eject").status_code == 403
    get_settings.cache_clear()


def test_cors_allows_vite_origin(client):
    r = client.options(
        "/api/health",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"


def _ts_interfaces() -> dict[str, set[str]]:
    text = TELEMETRY_TS.read_text()
    out = {}
    for m in re.finditer(r"export interface (\w+) \{(.*?)\n\}", text, re.S):
        out[m.group(1)] = set(re.findall(r"^\s+(\w+)\??:", m.group(2), re.M))
    return out


def test_pydantic_models_match_telemetry_ts_field_for_field():
    ts = _ts_interfaces()
    for model in schemas.CONTRACT_MODELS:
        name = model.__name__
        assert name in ts, f"{name} missing from telemetry.ts"
        assert set(model.model_json_schema()["properties"]) == ts[name], name


def test_file_scanned_contract_example_fields():
    required = {
        "type", "event_id", "timestamp", "scan_id", "drive", "file", "filename", "size_bytes",
        "sha256", "entropy", "chi_square", "magic_type", "magic_hex", "extension_mismatch",
        "yara_matches", "authenticode", "likelihood", "impact", "risk_score", "tier", "mitre",
        "reasons", "scan_status", "chain_index", "chain_hash",
    }
    assert required <= set(schemas.FileScannedEvent.model_fields)
    assert schemas.FileScannedEvent.model_config["extra"] == "allow"

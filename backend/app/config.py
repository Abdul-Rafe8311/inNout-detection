"""Environment-driven settings (AEGIS_* variables)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

ENTROPY_THRESHOLD = 7.2
CHUNK_SIZE = 64 * 1024


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    """Runtime configuration. Secrets come only from the environment / .env."""

    max_scan_file_size_mb: int
    scan_workers: int
    data_dir: Path
    retention_days: int
    redact_filenames: bool
    demo_mode: bool
    vault_passphrase: str
    hmac_secret: str
    local_ioc_path: Path
    mb_auth_key: str
    vt_api_key: str
    demo_drive_path: Path
    watch_usb: bool
    port: int

    @property
    def max_scan_file_size_bytes(self) -> int:
        return self.max_scan_file_size_mb * 1024 * 1024


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load settings once (reads backend/.env if present)."""
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    return Settings(
        max_scan_file_size_mb=int(os.getenv("AEGIS_MAX_SCAN_FILE_SIZE_MB", "50")),
        scan_workers=int(os.getenv("AEGIS_SCAN_WORKERS", "4")),
        data_dir=Path(os.getenv("AEGIS_DATA_DIR", "./data")).resolve(),
        retention_days=int(os.getenv("AEGIS_RETENTION_DAYS", "30")),
        redact_filenames=_bool("AEGIS_REDACT_FILENAMES", False),
        demo_mode=_bool("AEGIS_DEMO_MODE", True),
        vault_passphrase=os.getenv("AEGIS_VAULT_PASSPHRASE", ""),
        hmac_secret=os.getenv("AEGIS_HMAC_SECRET", ""),
        local_ioc_path=Path(os.getenv("AEGIS_LOCAL_IOC_PATH", "../qa_demo/local_ioc.txt")),
        mb_auth_key=os.getenv("AEGIS_MB_AUTH_KEY", ""),
        vt_api_key=os.getenv("AEGIS_VT_API_KEY", ""),
        demo_drive_path=Path(
            os.getenv("AEGIS_DEMO_DRIVE_PATH", "../qa_demo/sample_usb_drive")
        ).resolve(),
        watch_usb=_bool("AEGIS_WATCH_USB", True),
        port=int(os.getenv("AEGIS_PORT", "8000")),
    )

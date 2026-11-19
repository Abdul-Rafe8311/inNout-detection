import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "backend"))
sys.path.insert(0, str(ROOT))


@pytest.fixture(scope="session")
def drive(tmp_path_factory):
    """Fresh copy of the demo drive in a temp dir."""
    import generate_payloads as gp

    dest = tmp_path_factory.mktemp("usb")
    gp.generate(dest)
    return dest

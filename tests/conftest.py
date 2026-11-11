import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("GTOOLBOX_LAN", "0")

import main  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

BASE = "http://127.0.0.1:8000"


@pytest.fixture
def local_client():
    """A request coming from the host computer (desktop window)."""
    return TestClient(main.app, base_url=BASE, client=("127.0.0.1", 50000))


@pytest.fixture
def remote_client():
    """A request coming from another device on the LAN."""
    return TestClient(main.app, base_url="http://192.168.1.105:8000", client=("192.168.1.50", 50000),
                      follow_redirects=False)


@pytest.fixture
def lan_enabled(monkeypatch):
    monkeypatch.setenv("GTOOLBOX_LAN", "1")
    yield

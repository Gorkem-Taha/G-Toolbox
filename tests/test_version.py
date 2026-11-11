"""The version lives only in gtoolbox/__init__.py; everything else must derive from it."""
import re
from pathlib import Path

import gtoolbox
import gtoolbox.config as gt_config

ROOT = Path(__file__).resolve().parents[1]


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", gtoolbox.__version__)


def test_config_uses_package_version():
    assert gt_config.APP_VERSION == gtoolbox.__version__


def test_server_reports_version(local_client):
    assert local_client.get("/check-update").json()["current"] == gtoolbox.__version__


def test_no_hardcoded_versions():
    """App version numbers must not be duplicated in other files."""
    pattern = re.compile(r"(G-Toolbox/|\bv)4\.\d|versionName \"|versionCode \d|Toolbox v\d")
    for rel in ("launcher/Launcher.cs", "android/app/build.gradle", "static/js/app.js", "templates/index.html",
                *[str(p.relative_to(ROOT)) for p in (ROOT / "gtoolbox").rglob("*.py")]):
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert not pattern.search(text), f"hard-coded version in {rel}: {pattern.search(text).group(0)}"


def test_gradle_reads_package_version():
    gradle = (ROOT / "android/app/build.gradle").read_text(encoding="utf-8")
    assert "gtoolbox/__init__.py" in gradle and "versionName appVersionName" in gradle

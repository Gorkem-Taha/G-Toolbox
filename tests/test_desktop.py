"""desktop_app: theme detection for the AppImage control window."""
import subprocess
import types

import pytest

import desktop_app


@pytest.fixture(autouse=True)
def no_gsettings(monkeypatch, tmp_path):
    monkeypatch.delenv("GTK_THEME", raising=False)
    monkeypatch.setattr(desktop_app.Path, "home", classmethod(lambda cls: tmp_path))

    def fake_run(*a, **kw):
        raise FileNotFoundError("gsettings")
    monkeypatch.setattr(subprocess, "run", fake_run)


def test_light_by_default():
    assert desktop_app._system_prefers_dark() is False


def test_gtk_theme_dark(monkeypatch):
    monkeypatch.setenv("GTK_THEME", "Adwaita:dark")
    assert desktop_app._system_prefers_dark() is True


def test_gnome_color_scheme(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: types.SimpleNamespace(stdout="'prefer-dark'\n"))
    assert desktop_app._system_prefers_dark() is True
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: types.SimpleNamespace(stdout="'default'\n"))
    assert desktop_app._system_prefers_dark() is False


def test_kde_dark_scheme(tmp_path):
    (tmp_path / ".config").mkdir()
    (tmp_path / ".config" / "kdeglobals").write_text("[General]\nColorScheme=BreezeDark\n")
    assert desktop_app._system_prefers_dark() is True

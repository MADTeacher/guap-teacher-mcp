"""Offline tests for auth.py browser bootstrap (no network, no browser).

The install-on-demand path may run inside the stdio MCP server, where
stdout is the JSON-RPC channel: every message must go to stderr only.
"""

import types

from guap_teacher_mcp import auth


def _fake_subprocess(returncode=0, stderr=""):
    return types.SimpleNamespace(run=lambda cmd, **kw: types.SimpleNamespace(
        returncode=returncode, stderr=stderr
    ))


def test_probe_ok_no_output(monkeypatch, capsys):
    monkeypatch.setattr(auth, "_probe_chromium_sync", lambda: True)
    assert auth._ensure_playwright_browsers() is True
    captured = capsys.readouterr()
    assert captured.out == ""  # stdout is the stdio JSON-RPC channel
    assert captured.err == ""


def test_install_on_demand_writes_to_stderr_only(monkeypatch, capsys):
    monkeypatch.setattr(auth, "_probe_chromium_sync", lambda: False)
    monkeypatch.setattr(auth, "subprocess", _fake_subprocess(returncode=0))
    assert auth._ensure_playwright_browsers() is True
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Installing Playwright Chromium" in captured.err
    assert "installed" in captured.err


def test_install_failure_reports_to_stderr(monkeypatch, capsys):
    monkeypatch.setattr(auth, "_probe_chromium_sync", lambda: False)
    monkeypatch.setattr(auth, "subprocess", _fake_subprocess(returncode=1, stderr="boom"))
    assert auth._ensure_playwright_browsers() is False
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "boom" in captured.err

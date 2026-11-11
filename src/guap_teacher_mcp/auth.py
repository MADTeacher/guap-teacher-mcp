"""Playwright-based authentication for pro.guap.ru.

Opens a browser, the teacher logs in through GUAP SSO (Keycloak) manually,
and the resulting session cookies are stored for reuse by the HTTP client.
No credentials are ever handled by this code.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

GUAP_URL = "https://pro.guap.ru"
# Any /inside/* page redirects to the SSO login when not authenticated,
# so it doubles as a convenient login entry point.
LOGIN_ENTRY_URL = f"{GUAP_URL}/inside/profile"

DEFAULT_SESSION_DIR = Path.home() / ".guap-teacher-mcp"


def session_path() -> Path:
    """Session cookie file location (overridable via GUAP_SESSION_PATH)."""
    env = os.environ.get("GUAP_SESSION_PATH")
    return Path(env) if env else DEFAULT_SESSION_DIR / "session.json"


def load_cookie_string(path: Optional[Path] = None) -> Optional[str]:
    """Return stored cookies as a 'name=value; ...' header, or None."""
    path = path or session_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    cookies = [c for c in data.get("cookies", []) if "guap.ru" in (c.get("domain") or "")]
    if not cookies:
        return None
    return "; ".join(f"{c['name']}={c['value']}" for c in cookies)


def _probe_chromium_sync() -> bool:
    """Try launching Chromium in a private event loop (safe in any thread)."""
    from playwright.async_api import async_playwright

    try:
        asyncio.run(_try_launch(async_playwright))
        return True
    except Exception:
        return False


def _ensure_playwright_browsers() -> bool:
    """Check that Chromium is available; install it on demand.

    Runs the probe in a worker thread: this function may be called from a
    running event loop (the MCP server context), where asyncio.run() is
    forbidden and would silently orphan the coroutine.
    """
    try:
        from playwright.async_api import async_playwright  # noqa: F401
    except ImportError:
        return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        if pool.submit(_probe_chromium_sync).result():
            return True

    # Never stdout: inside the stdio MCP server it is the JSON-RPC channel.
    print(
        "Installing Playwright Chromium (this may take 1-2 minutes)...",
        file=sys.stderr,
    )
    try:
        result = subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode == 0:
            print("Playwright Chromium installed.", file=sys.stderr)
            return True
        print(f"playwright install failed: {result.stderr}", file=sys.stderr)
        return False
    except Exception as exc:  # pragma: no cover - environment-dependent
        print(f"playwright install error: {exc}", file=sys.stderr)
        return False


async def _try_launch(async_playwright: Any) -> None:
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        await browser.close()


async def authenticate_with_browser(
    save_path: Optional[Path] = None,
    timeout_s: int = 180,
    headless: bool = False,
) -> dict[str, Any]:
    """Log in via a real browser and persist session cookies.

    The browser opens pro.guap.ru and redirects to the GUAP SSO login form.
    The user enters their credentials manually (headless=False recommended);
    once the browser lands back on an /inside/* page, cookies are collected.

    Returns a dict with 'success' and either 'cookie_count'/'save_path'
    or 'error'.
    """
    from playwright.async_api import async_playwright

    save_path = save_path or session_path()

    if not _ensure_playwright_browsers():
        return {"success": False, "error": "Playwright Chromium is not available"}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(LOGIN_ENTRY_URL, wait_until="domcontentloaded")
            # Wait until the user completes SSO and returns to the cabinet.
            await page.wait_for_url(
                f"{GUAP_URL}/inside/**", timeout=timeout_s * 1000
            )
            # Give the server a moment to set the final session cookies.
            await page.wait_for_load_state("networkidle", timeout=30_000)

            cookies = await context.cookies()
            await browser.close()
    except Exception as exc:
        return {"success": False, "error": f"Login did not complete: {exc}"}

    guap_cookies = [c for c in cookies if "guap.ru" in (c.get("domain") or "")]
    if not guap_cookies:
        return {"success": False, "error": "No guap.ru cookies captured"}

    save_path.parent.mkdir(parents=True, exist_ok=True)
    save_path.write_text(
        json.dumps(
            {
                "saved_at": datetime.now(timezone.utc).isoformat(),
                "cookies": cookies,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return {
        "success": True,
        "cookie_count": len(guap_cookies),
        "save_path": str(save_path),
    }

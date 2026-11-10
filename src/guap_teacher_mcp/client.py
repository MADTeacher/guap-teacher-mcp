"""HTTP client for the server-rendered pro.guap.ru pages.

pro.guap.ru has no public JSON API: the cabinet is a set of Laravel-rendered
HTML pages guarded by session cookies (PHPSESSID) issued after Keycloak SSO.
This client carries those cookies and never follows redirects, so that
"302 -> oauth/login" can be reported as an auth failure instead of silently
parsing the login page.
"""

from __future__ import annotations

from typing import Optional

import httpx

BASE_URL = "https://pro.guap.ru"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


class NotAuthenticatedError(RuntimeError):
    """Raised when an action requires a stored session that is missing."""


class GuapClient:
    """Cookie-authenticated HTTP client for /inside/* pages."""

    def __init__(self, cookie: str):
        self._client = httpx.Client(
            base_url=BASE_URL,
            headers={"Cookie": cookie, "User-Agent": USER_AGENT},
            timeout=30.0,
            follow_redirects=False,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "GuapClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def get(
        self, path: str, params: Optional[dict[str, str | int]] = None
    ) -> httpx.Response:
        """GET an /inside/* page. Redirects are NOT followed."""
        response = self._client.get(path, params=params)
        return response

    def post_form(
        self, path: str, data: dict[str, str] | list[tuple[str, str]]
    ) -> httpx.Response:
        """POST a form to an /inside/* route (Laravel method overrides such
        as _method=PATCH are carried in `data`). Redirects are NOT followed,
        so a 302 after a successful submit can be told apart from errors."""
        return self._client.post(
            path, data=data, headers={"Referer": BASE_URL + path}
        )

    def post_multipart(
        self,
        path: str,
        data: dict[str, str] | list[tuple[str, str]],
        files: Optional[dict[str, tuple[str, bytes]]] = None,
    ) -> httpx.Response:
        """POST a multipart/form-data form (file uploads; `files` maps the
        input name to (filename, payload) tuples, e.g. {"file": ("a.pdf",
        b"...")}). Redirects are NOT followed, same contract as post_form."""
        return self._client.post(
            path,
            data=data,
            files=files or {},
            headers={"Referer": BASE_URL + path},
        )

    def check_session(self) -> tuple[bool, str]:
        """Check whether the stored session is still valid.

        Returns (is_valid, human_readable_status).
        """
        try:
            response = self.get("/inside/profile")
        except httpx.HTTPError as exc:
            return False, f"network error: {exc}"

        if response.status_code in (301, 302, 303, 307, 308):
            location = response.headers.get("location", "?")
            return False, f"not authenticated (redirect to {location})"
        if response.status_code == 404:
            return False, "HTTP 404 for /inside/profile (unexpected)"
        if response.status_code == 200:
            if "kc-form-login" in response.text:
                return False, "SSO login form returned instead of profile"
            return True, "session is valid"
        return False, f"HTTP {response.status_code}"

"""Route discovery for the teacher side of pro.guap.ru.

The teacher-facing routes are not documented anywhere public, so this module
walks the authenticated cabinet, collects every /inside/* link it can see and
probes them (politely, with a delay) to build a route map:

    pattern  ->  path with numeric ids replaced by {id}
    status   ->  HTTP status (200 = real page for this account,
                 302 = login redirect, 404 = not a route,
                 0 = seen as a link but not probed yet)
    title    ->  page title (h3.page__title or <title>)
    found_on ->  page where the link was first seen ("" for start pages)

The map is the foundation for later teacher tools: task lists, student
report download, grading. Keep it read-only.
"""

from __future__ import annotations

import re
import time
from collections import deque
from dataclasses import asdict, dataclass
from typing import Optional

from bs4 import BeautifulSoup

from .client import GuapClient

NUMERIC_SEGMENT = re.compile(r"/\d+(?=[/?#]|$)")

DEFAULT_START_PATH = "/inside/profile"


@dataclass
class RouteInfo:
    pattern: str
    status: int
    redirect: Optional[str] = None
    title: Optional[str] = None
    found_on: str = ""


def normalize_pattern(path: str) -> str:
    """Collapse numeric path segments: /inside/profile/123 -> /inside/profile/{id}."""
    return NUMERIC_SEGMENT.sub("/{id}", path)


def extract_inside_links(html: str) -> set[str]:
    """Collect absolute /inside/* paths (without query strings) from a page."""
    soup = BeautifulSoup(html, "html.parser")
    links: set[str] = set()
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href:
            continue
        if href.startswith("http") and "://pro.guap.ru" not in href:
            continue  # external link (e.g. Google Drive)
        path = href.split("://pro.guap.ru", 1)[-1]
        path = path.split("?", 1)[0].split("#", 1)[0]
        path = path.rstrip("/") or path
        if path.startswith("/inside") and path != "/inside":
            links.add(path)
    return links


def extract_inside_links_labeled(html: str) -> list[dict[str, str]]:
    """Collect /inside/* links with their anchor texts, sorted by path."""
    soup = BeautifulSoup(html, "html.parser")
    labeled: dict[str, str] = {}
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href:
            continue
        if href.startswith("http") and "://pro.guap.ru" not in href:
            continue
        path = href.split("://pro.guap.ru", 1)[-1]
        path = path.split("?", 1)[0].split("#", 1)[0]
        path = path.rstrip("/") or path
        if not path.startswith("/inside") or path == "/inside":
            continue
        text = anchor.get_text(" ", strip=True)
        labeled.setdefault(path, text)
    return [{"path": p, "text": t} for p, t in sorted(labeled.items())]


def page_title(html: str) -> Optional[str]:
    """Best-effort page title: h3.page__title first, then <title>."""
    soup = BeautifulSoup(html, "html.parser")
    node = soup.select_one("h3.page__title") or soup.title
    if node is None:
        return None
    text = node.get_text(" ", strip=True)
    return text[:120] or None


def _register_seen(routes: dict[str, RouteInfo], pattern: str, found_on: str) -> None:
    """Record a pattern discovered as a link on another page (not probed yet)."""
    if pattern not in routes:
        routes[pattern] = RouteInfo(pattern=pattern, status=0, found_on=found_on)


def discover_routes(
    client: GuapClient,
    start_paths: tuple[str, ...] = (DEFAULT_START_PATH,),
    crawl: bool = False,
    max_requests: int = 40,
    delay_s: float = 0.3,
) -> dict:
    """Walk the cabinet and build a route map.

    Always: fetch the start pages, probe every /inside/* link found there.
    With crawl=True also parse each successfully probed page for more links
    (breadth-first). Total GET requests are bounded by max_requests.
    """
    routes: dict[str, RouteInfo] = {}
    start_set = set(start_paths)
    # (path, extract_links) pairs: only start pages are parsed for links
    # unless crawl=True.
    queue: deque[tuple[str, bool]] = deque(
        (path, True) for path in dict.fromkeys(start_paths)
    )
    queued = {path for path, _ in queue}

    requests_done = 0
    while queue and requests_done < max_requests:
        path, want_links = queue.popleft()

        response = client.get(path)
        requests_done += 1
        time.sleep(delay_s)

        pattern = normalize_pattern(path)
        info = routes.get(pattern)
        if info is None:
            info = RouteInfo(pattern=pattern, status=response.status_code)
            routes[pattern] = info
        info.status = response.status_code
        info.redirect = response.headers.get("location")

        if response.status_code == 200:
            if "kc-form-login" in response.text:
                info.title = "SSO login form (session expired?)"
            else:
                info.title = page_title(response.text)
                if want_links:
                    for link in sorted(extract_inside_links(response.text)):
                        _register_seen(routes, normalize_pattern(link), path)
                        if crawl and link not in queued:
                            queued.add(link)
                            queue.append((link, crawl))

    ordered = sorted(
        routes.values(),
        key=lambda r: (r.status != 200, r.pattern),
    )
    return {
        "requests_done": requests_done,
        "routes": [asdict(r) for r in ordered],
        "hint": "status=0 means the link was seen but not probed yet; "
        "raise max_requests or set crawl=True to probe everything",
    }

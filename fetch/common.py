"""Shared paths and a polite HTTP client for the fetch scripts."""
from __future__ import annotations

import time
from pathlib import Path

import requests

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
HERE = Path(__file__).resolve().parent

session = requests.Session()
session.headers["User-Agent"] = "stylometry-research-script/1.0"


def request(method: str, url: str, delay: float = 1.2, tries: int = 4, **kw) -> requests.Response:
    """One request, then a pause of `delay` seconds. Network errors, 429 and 5xx are retried with backoff;
    any other response is returned for the caller to check."""
    for attempt in range(tries):
        try:
            r = session.request(method, url, timeout=180, **kw)
        except requests.RequestException as e:
            print("  network error:", e)
            time.sleep(10 * (attempt + 1))
            continue
        time.sleep(delay)
        if r.status_code != 429 and r.status_code < 500:
            return r
        print("  HTTP", r.status_code, url)
        time.sleep(int(r.headers.get("retry-after") or 0) + 10 * (attempt + 1))
    raise RuntimeError(f"giving up on {url}")


def download(url: str, path: Path, delay: float = 1.2) -> bytes:
    """Save `url` to `path` unless it is already there; return the file's bytes."""
    if path.exists() and path.stat().st_size > 0:
        return path.read_bytes()
    r = request("GET", url, delay)
    r.raise_for_status()
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    part.write_bytes(r.content)
    part.replace(path)
    print("  saved", path.relative_to(RAW.parent.parent), len(r.content), "bytes")
    return r.content

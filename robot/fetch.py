"""Download the Habous month and Hijri files. Polite: clear User-Agent, pause between requests, 3 tries."""
from __future__ import annotations

import time

import requests

BASE = "https://www.habous.gov.ma/data/"
USER_AGENT = "PrayMaBot/1.0 (+https://github.com/abdelkader-zaglou/prayma-data)"
PAUSE_S = 1.5
TRIES = 3
TIMEOUT_S = 30

_last_request = 0.0


def _get(url: str) -> str | None:
    """Text of [url], or None when it does not exist (404). Raises after 3 failed tries."""
    global _last_request
    error: Exception | None = None
    for attempt in range(TRIES):
        wait = _last_request + PAUSE_S - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        try:
            r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_S)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.text
        except requests.RequestException as e:
            error = e
            time.sleep(2 ** attempt * 5)
    raise RuntimeError(f"cannot download {url}: {error}")


def fetch_month(year: int, month: int) -> str | None:
    """The month file for all cities, or None if Habous has not published it yet."""
    return _get(f"{BASE}horaires-{year}-{month:02d}.js")


def fetch_hijri() -> str:
    """The official Hijri month starts."""
    text = _get(f"{BASE}hijri.js")
    if text is None:
        raise RuntimeError("hijri.js is missing on habous.gov.ma")
    return text

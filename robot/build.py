"""Write month files + manifest into site/, sign the manifest ."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .morocco import ORDER, morocco_offset, offset_string
from .signing import sign

SCHEMA = 1


def _dump(obj) -> bytes:
    # Stable bytes: sorted keys, no spaces, UTF-8. The signature covers these exact bytes.
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def month_file(month: str, cities: dict[str, list[list[str]]], imsak: dict | None = None) -> bytes:
    y, m = map(int, month.split("-"))
    first = datetime(y, m, 1, 12, tzinfo=timezone.utc)
    return _dump({
        "schema": SCHEMA, "month": month, "zone": "Africa/Casablanca",
        "utcOffset": offset_string(morocco_offset(first)),
        "order": ORDER, "cities": cities, "imsak": imsak,
    })


def publish(site: Path, months: dict[str, bytes], kinds: dict[str, str], hijri: list[dict],
            private_pem: bytes, notice: dict | None = None, now: datetime | None = None) -> bool:
    """Write files; bump version only if any content changed. Returns True when something changed."""
    now = now or datetime.now(timezone.utc)
    (site / "times").mkdir(parents=True, exist_ok=True)
    old_path = site / "manifest.json"
    old = json.loads(old_path.read_text("utf-8")) if old_path.exists() else {"version": 0, "months": [], "hijri": []}

    entries = []
    for month in sorted(months):
        data = months[month]
        (site / "times" / f"{month}.json").write_bytes(data)
        entries.append({"month": month, "path": f"times/{month}.json", "sha256": hashlib.sha256(data).hexdigest(),
                        "bytes": len(data), "kind": kinds.get(month, "official")})

    changed = (entries != old.get("months") or hijri != old.get("hijri") or notice != old.get("notice"))
    if not changed:
        return False
    manifest = {"schema": SCHEMA, "version": int(old.get("version", 0)) + 1,
                "generatedAt": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "source": "habous.gov.ma",
                "minAppVersionCode": 1, "months": entries, "hijri": hijri, "notice": notice}
    raw = _dump(manifest)
    old_path.write_bytes(raw)
    (site / "manifest.sig").write_text(sign(raw, private_pem))
    return True

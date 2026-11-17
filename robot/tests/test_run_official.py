"""A full official run with the saved Habous files instead of the network."""
import json
import sys
from datetime import date
from pathlib import Path

from robot import run
from robot.signing import generate_pem

SAMPLES = Path(__file__).parent / "samples"


def test_official_run_publishes_signed_official_files(tmp_path, monkeypatch):
    priv, _ = generate_pem()
    monkeypatch.setenv("PRAYMA_SIGNING_KEY", priv.decode())
    monkeypatch.setattr(run, "date", type("D", (), {"today": staticmethod(lambda: date(2026, 11, 14))}))
    monkeypatch.setattr(run, "fetch_month", lambda y, m: (SAMPLES / f"horaires-{y}-{m:02d}.js").read_text("utf-8"))
    monkeypatch.setattr(run, "fetch_hijri", lambda: (SAMPLES / "hijri.js").read_text("utf-8"))
    monkeypatch.setattr(sys, "argv", ["run", "--site", str(tmp_path)])

    assert run.main() == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text("utf-8"))
    assert [(m["month"], m["kind"]) for m in manifest["months"]] == [("2026-11", "official")]
    assert manifest["hijri"][-1]["start"] == "2026-11-11"
    month = json.loads((tmp_path / "times" / "2026-11.json").read_text("utf-8"))
    assert month["utcOffset"] == "+00:00"
    assert month["cities"]["casablanca"][13] == ["05:30", "06:58", "12:20", "15:08", "17:33", "18:49"]
    assert (tmp_path / "manifest.sig").read_text().strip()


def test_next_month_not_published_yet_is_skipped(tmp_path, monkeypatch):
    priv, _ = generate_pem()
    monkeypatch.setenv("PRAYMA_SIGNING_KEY", priv.decode())
    monkeypatch.setattr(run, "date", type("D", (), {"today": staticmethod(lambda: date(2026, 11, 25))}))
    monkeypatch.setattr(
        run, "fetch_month", lambda y, m: (SAMPLES / "horaires-2026-11.js").read_text("utf-8") if m == 11 else None
    )
    monkeypatch.setattr(run, "fetch_hijri", lambda: (SAMPLES / "hijri.js").read_text("utf-8"))
    monkeypatch.setattr(sys, "argv", ["run", "--site", str(tmp_path)])

    assert run.main() == 0
    manifest = json.loads((tmp_path / "manifest.json").read_text("utf-8"))
    assert [m["month"] for m in manifest["months"]] == ["2026-11"]

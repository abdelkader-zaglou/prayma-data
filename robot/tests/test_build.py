import json

from robot.build import month_file, publish
from robot.signing import generate_pem, verify


def test_publish_signs_and_bumps_version_only_on_change(tmp_path):
    priv, pub = generate_pem()
    mf = month_file("2026-11", {"casablanca": [["05:30", "06:58", "12:20", "15:07", "17:33", "18:49"]]})
    assert json.loads(mf)["utcOffset"] == "+00:00"

    assert publish(tmp_path, {"2026-11": mf}, {}, [], priv) is True
    raw = (tmp_path / "manifest.json").read_bytes()
    assert verify(raw, (tmp_path / "manifest.sig").read_text(), pub)
    assert json.loads(raw)["version"] == 1

    assert publish(tmp_path, {"2026-11": mf}, {}, [], priv) is False      # same data: no new version
    mf2 = month_file("2026-11", {"casablanca": [["05:31", "06:58", "12:20", "15:07", "17:33", "18:49"]]})
    assert publish(tmp_path, {"2026-11": mf2}, {}, [], priv) is True
    assert json.loads((tmp_path / "manifest.json").read_bytes())["version"] == 2


def test_tampered_manifest_fails_verification(tmp_path):
    priv, pub = generate_pem()
    publish(tmp_path, {"2026-11": month_file("2026-11", {})}, {}, [], priv)
    raw = (tmp_path / "manifest.json").read_bytes().replace(b'"version":1', b'"version":9')
    assert not verify(raw, (tmp_path / "manifest.sig").read_text(), pub)

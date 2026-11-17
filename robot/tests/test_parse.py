"""The Habous reader, on saved real files."""
from pathlib import Path

import pytest

from robot import cities, validate
from robot.parse import ParseError, parse_hijri, parse_month
from robot.run import official_month

SAMPLES = Path(__file__).parent / "samples"


def sample(name: str) -> str:
    return (SAMPLES / name).read_text(encoding="utf-8")


def test_november_2026():
    hm = parse_month(sample("horaires-2026-11.js"))
    assert (hm.year, hm.month, hm.timezone) == (2026, 11, "GMT")
    assert len(hm.cities) == 190
    assert all(len(days) == 30 for days in hm.cities.values())
    assert hm.names[58] == "الدار البيضاء"
    assert hm.cities[58][13] == ["05:30", "06:58", "12:20", "15:08", "17:33", "18:49"]


def test_october_has_31_days():
    hm = parse_month(sample("horaires-2026-10.js"))
    assert all(len(days) == 31 for days in hm.cities.values())


def test_every_city_of_ours_passes_the_safety_checks_on_real_data():
    city_list = cities.load()
    for name, (y, m) in (("horaires-2026-10.js", (2026, 10)), ("horaires-2026-11.js", (2026, 11))):
        per_city = official_month(parse_month(sample(name)), y, m, city_list)
        assert len(per_city) == len(city_list)
        for c in city_list:
            validate.check_city_month(c, y, m, per_city[c.id])


def test_sale_and_temara_use_rabat():
    per_city = official_month(parse_month(sample("horaires-2026-11.js")), 2026, 11, cities.load())
    assert per_city["sale"] == per_city["rabat"] == per_city["temara"]


def test_a_changed_format_is_refused():
    with pytest.raises(ParseError):
        parse_month("var x = 1;")
    with pytest.raises(ParseError):
        parse_month(sample("horaires-2026-11.js").replace('"Ishae"', '"Isha"'))
    with pytest.raises(ParseError):
        parse_month(sample("horaires-2026-11.js").replace('"fuseau":"GMT"', '"fuseau":"GMT+1"'))


def test_wrong_month_is_refused():
    with pytest.raises(RuntimeError):
        official_month(parse_month(sample("horaires-2026-11.js")), 2026, 12, cities.load())


def test_hijri_official_starts():
    entries = parse_hijri(sample("hijri.js"))
    assert entries[-1] == {"y": 1448, "m": 6, "start": "2026-11-11", "official": True}
    assert [e["start"] for e in entries] == sorted(e["start"] for e in entries)
    with pytest.raises(ParseError):
        parse_hijri("window.HIJRI = {};")

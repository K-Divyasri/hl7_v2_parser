"""Tests for the ORU extractor against generated lab-result messages."""

from hl7lib import make_oru, parse_oru


def test_oru_metadata_and_patient():
    d = parse_oru(make_oru(seed=1))
    assert d["message"]["message_type"] == "ORU"
    assert d["message"]["trigger_event"] == "R01"
    assert d["patient"]["patient_id"].startswith("MRN")


def test_oru_order_and_observations():
    d = parse_oru(make_oru(seed=1))
    assert len(d["orders"]) == 1
    order = d["orders"][0]
    assert order["service"]["text"] == "Comprehensive metabolic panel"
    obs = order["observations"]
    assert len(obs) == 5                       # the lab panel has five analytes
    assert all(o["status"] == "F" for o in obs)
    assert all(o["value_type"] == "NM" for o in obs)


def test_oru_has_loinc_codes_and_flags():
    obs = parse_oru(make_oru(seed=1))["orders"][0]["observations"]
    codes = {o["code"] for o in obs}
    assert "2345-7" in codes                   # Glucose LOINC code
    assert all(o["code_system"] == "LN" for o in obs)
    assert all(o["abnormal_flag"] in ("H", "L", "N") for o in obs)
    assert all(o["units"] != "" for o in obs)

"""Tests for the ADT extractor against generated messages."""

from hl7lib import make_adt, parse_adt


def test_adt_message_metadata():
    d = parse_adt(make_adt(seed=1))
    assert d["message"]["message_type"] == "ADT"
    assert d["message"]["trigger_event"] == "A01"
    assert d["message"]["control_id"] != ""
    assert d["message"]["version"] == "2.5.1"


def test_adt_patient():
    d = parse_adt(make_adt(seed=1))
    p = d["patient"]
    assert p["patient_id"].startswith("MRN")
    assert p["name"]["family"] != ""
    assert p["name"]["given"] != ""
    assert p["sex"] in ("M", "F")
    assert len(p["date_of_birth"]) == 8  # YYYYMMDD
    assert p["address"]["state"] != ""


def test_adt_visit():
    d = parse_adt(make_adt(seed=1))
    v = d["visit"]
    assert v["patient_class"] in ("I", "O", "E")
    assert v["attending_doctor"]["family"] != ""
    assert v["admit_date"] != ""


def test_adt_accepts_message_object():
    from hl7lib import parse
    m = parse(make_adt(seed=2))
    d = parse_adt(m)  # should accept a Message, not only a string
    assert d["patient"]["patient_id"].startswith("MRN")

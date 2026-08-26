"""Tests for the core parser: delimiters, fields, components, subcomponents,
repetitions, and the MSH special-casing."""

from hl7lib import parse

# A controlled message exercising every level of the hierarchy. Note PID-3 has a
# subcomponent (H&S) and PID-13 has two repetitions (two phone numbers).
MSG = (
    "MSH|^~\\&|A|B|C|D|20240101000000||ADT^A01|CTRL1|P|2.5.1\r"
    "PID|1||MRN1^^^H&S^MR||DOE^JANE^Q||19900101|F|||1 RD^^TOWN^MA^02000||555-1111~555-2222\r"
)


def test_encoding_characters_read_from_msh():
    m = parse(MSG)
    assert m.enc["field"] == "|"
    assert m.enc["comp"] == "^"
    assert m.enc["rep"] == "~"
    assert m.enc["sub"] == "&"


def test_msh_fields_indexed_correctly():
    m = parse(MSG)
    assert m.get("MSH", 9) == "ADT^A01"
    assert m.get("MSH", 9, comp=1) == "ADT"
    assert m.get("MSH", 9, comp=2) == "A01"
    assert m.get("MSH", 10) == "CTRL1"
    assert m.get("MSH", 12) == "2.5.1"


def test_components():
    m = parse(MSG)
    assert m.get("PID", 5, comp=1) == "DOE"
    assert m.get("PID", 5, comp=2) == "JANE"
    assert m.get("PID", 5, comp=3) == "Q"
    assert m.get("PID", 8) == "F"


def test_subcomponents():
    m = parse(MSG)
    # PID-3 component 4 is "H&S" - two subcomponents.
    assert m.get("PID", 3, comp=4) == "H&S"
    assert m.get("PID", 3, comp=4, sub=1) == "H"
    assert m.get("PID", 3, comp=4, sub=2) == "S"


def test_repetitions():
    m = parse(MSG)
    assert m.get("PID", 13, rep=0) == "555-1111"
    assert m.get("PID", 13, rep=1) == "555-2222"


def test_missing_pieces_return_empty():
    m = parse(MSG)
    assert m.get("PID", 99) == ""          # field out of range
    assert m.get("OBX", 5) == ""           # no OBX segment
    assert m.get("PID", 5, comp=9) == ""   # component out of range


def test_repeating_segments():
    msg = MSG + "DG1|1|||Flu\rDG1|2|||Cough\r"
    m = parse(msg)
    assert len(m.segments_named("DG1")) == 2
    assert m.get("DG1", 4, occ=0) == "Flu"
    assert m.get("DG1", 4, occ=1) == "Cough"

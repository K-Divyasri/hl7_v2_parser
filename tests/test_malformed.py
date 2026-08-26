"""Tests that bad input fails clearly, and missing data degrades gracefully."""

import pytest

from hl7lib import parse, parse_message, HL7ParseError


def test_empty_message_raises():
    with pytest.raises(HL7ParseError):
        parse("")
    with pytest.raises(HL7ParseError):
        parse("   ")


def test_message_without_msh_raises():
    with pytest.raises(HL7ParseError):
        parse("PID|1||MRN1||DOE^JANE")


def test_truncated_msh_raises():
    with pytest.raises(HL7ParseError):
        parse("MSH|^")  # too short to hold encoding characters


def test_missing_fields_are_empty_not_errors():
    # A valid header but no PID - asking for patient fields just returns "".
    m = parse("MSH|^~\\&|A|B|C|D|20240101||ADT^A01|C1|P|2.5.1")
    assert m.get("PID", 5) == ""
    assert m.get("MSH", 99) == ""


def test_unknown_message_type_falls_back():
    # An ORM (order) message we don't have a dedicated extractor for still parses.
    raw = "MSH|^~\\&|A|B|C|D|20240101||ORM^O01|C1|P|2.5.1\rPID|1||MRN9||X^Y"
    result = parse_message(raw)
    assert result["message"]["message_type"] == "ORM"
    assert any(s["segment"] == "PID" for s in result["segments"])

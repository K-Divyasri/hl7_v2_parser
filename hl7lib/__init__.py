"""hl7lib - a small, readable HL7 v2 parser plus ADT/ORU extractors.

    from hl7lib import parse, parse_message, parse_adt, parse_oru, make_adt
"""
from .parser import parse, Message, Segment, HL7ParseError
from .fields import annotate, describe_segment, FIELD_NAMES, SEGMENT_NAMES
from .adt import parse_adt, read_msh, read_pid, read_pv1
from .oru import parse_oru
from .generate import make_adt, make_oru, write_samples


def parse_message(raw):
    """Parse a raw message and dispatch to the right extractor based on the message
    type in MSH-9. ADT and ORU get full structured output; anything else falls back
    to the header plus an annotated segment dump so you still get something useful."""
    m = parse(raw)
    message_type = m.get("MSH", 9, comp=1)
    if message_type == "ADT":
        return parse_adt(m)
    if message_type == "ORU":
        return parse_oru(m)
    return {"message": read_msh(m), "segments": annotate(m)}


__all__ = [
    "parse", "Message", "Segment", "HL7ParseError",
    "annotate", "describe_segment", "FIELD_NAMES", "SEGMENT_NAMES",
    "parse_adt", "read_msh", "read_pid", "read_pv1",
    "parse_oru",
    "make_adt", "make_oru", "write_samples",
    "parse_message",
]

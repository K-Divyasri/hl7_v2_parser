"""A small, from-scratch HL7 v2 parser.

You could pip install a library (hl7apy, python-hl7) and we show those in the
knowledge notes. But writing the parser yourself, once, is the fastest way to
actually understand HL7 - and "I understand HL7 at the byte level" is the thing an
integration interview is really checking.

The whole format is just nested delimiters:

    segments      separated by a carriage return (\\r)
      fields      separated by |        (the field separator)
        repeats   separated by ~        (a field can occur more than once)
          comps   separated by ^        (components within a field)
            subs  separated by &        (subcomponents within a component)

The clever part: a message declares its own delimiters in its first segment.
MSH-1 IS the field separator (the 4th character of the message), and MSH-2 holds
the other four encoding characters, normally "^~\\&". So the message tells you how
to read the message. We read those first, then use them for everything else.
"""
from __future__ import annotations


class HL7ParseError(ValueError):
    """Raised when a message can't be parsed (empty, no MSH, too short, ...)."""


def _split_segments(raw: str):
    """HL7's real segment terminator is \\r. Files in the wild sometimes use \\n or
    \\r\\n, so we tolerate all three rather than choke on a stray newline."""
    text = raw.replace("\r\n", "\r").replace("\n", "\r")
    return [line for line in text.split("\r") if line.strip()]


class Segment:
    """One line of the message: a 3-letter name plus its fields.

    Field numbering is 1-based to match how HL7 people talk: PID-5 is the 5th
    field. Internally that's fields[4]. The get() method does the component and
    subcomponent splitting on demand.
    """

    def __init__(self, name, fields, enc):
        self.name = name
        self.fields = fields  # field n is fields[n-1]
        self.enc = enc        # {"field","comp","rep","esc","sub"}

    def field(self, n: int) -> str:
        """The raw text of field n (everything, repeats and components included)."""
        return self.fields[n - 1] if 1 <= n <= len(self.fields) else ""

    def get(self, n, comp=None, sub=None, rep=0) -> str:
        """Drill into field n -> repetition `rep` -> component `comp` -> sub `sub`.
        Component/subcomponent are 1-based; rep is 0-based. Missing pieces return ""
        rather than blowing up - real feeds are full of empty fields."""
        raw = self.field(n)
        if raw == "":
            return ""
        reps = raw.split(self.enc["rep"])
        chunk = reps[rep] if 0 <= rep < len(reps) else ""
        if comp is None:
            return chunk
        comps = chunk.split(self.enc["comp"])
        value = comps[comp - 1] if 1 <= comp <= len(comps) else ""
        if sub is None:
            return value
        subs = value.split(self.enc["sub"])
        return subs[sub - 1] if 1 <= sub <= len(subs) else ""

    def __repr__(self):
        return f"<Segment {self.name} ({len(self.fields)} fields)>"


class Message:
    """A parsed message: an ordered list of segments plus the encoding characters.

    Segments can repeat (many OBX in a lab result), so we keep them in order and
    let you pick an occurrence.
    """

    def __init__(self, segments, enc):
        self.segments = segments
        self.enc = enc

    def segment(self, name, occ=0):
        matches = [s for s in self.segments if s.name == name]
        return matches[occ] if 0 <= occ < len(matches) else None

    def segments_named(self, name):
        return [s for s in self.segments if s.name == name]

    def get(self, name, n, comp=None, sub=None, rep=0, occ=0) -> str:
        seg = self.segment(name, occ)
        return seg.get(n, comp, sub, rep) if seg else ""

    def __repr__(self):
        names = ", ".join(s.name for s in self.segments)
        return f"<Message [{names}]>"


def parse(raw: str) -> Message:
    """Parse a raw HL7 v2 message string into a Message. Raises HL7ParseError on
    anything that isn't a sane message."""
    if not raw or not raw.strip():
        raise HL7ParseError("Empty message")

    lines = _split_segments(raw)
    if not lines:
        raise HL7ParseError("No segments found")

    header = lines[0]
    if not header.startswith("MSH"):
        raise HL7ParseError(f"A message must start with MSH, got {header[:3]!r}")
    if len(header) < 8:
        raise HL7ParseError("MSH is too short to hold the encoding characters")

    # The message defines its own delimiters. MSH-1 is the 4th char; MSH-2 is the
    # next four (component, repetition, escape, subcomponent).
    field_sep = header[3]
    enc_chars = header[4:8]
    enc = {
        "field": field_sep,
        "comp": enc_chars[0],
        "rep": enc_chars[1],
        "esc": enc_chars[2],
        "sub": enc_chars[3],
    }

    segments = []
    for line in lines:
        if line[:3] == "MSH":
            # MSH is special: MSH-1 is the field separator itself, MSH-2 the
            # encoding chars. Re-line the fields so MSH-n indexes correctly.
            parts = line.split(field_sep)
            fields = [field_sep] + parts[1:]
            segments.append(Segment("MSH", fields, enc))
        else:
            parts = line.split(field_sep)
            segments.append(Segment(parts[0], parts[1:], enc))

    return Message(segments, enc)

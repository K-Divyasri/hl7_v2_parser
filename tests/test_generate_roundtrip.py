"""Round-trip tests: what the generator builds, the parser reads back correctly,
and the dispatcher routes to the right extractor."""

from hl7lib import make_adt, make_oru, parse_message, annotate, parse


def test_dispatch_adt():
    out = parse_message(make_adt(seed=5))
    assert out["message"]["message_type"] == "ADT"
    assert "visit" in out


def test_dispatch_oru():
    out = parse_message(make_oru(seed=5))
    assert out["message"]["message_type"] == "ORU"
    assert "orders" in out
    assert len(out["orders"][0]["observations"]) == 5


def test_annotate_lists_segments():
    ann = annotate(parse(make_adt(seed=6)))
    seg_names = {s["segment"] for s in ann}
    assert {"MSH", "PID", "PV1"} <= seg_names
    # Every annotated field carries a human-readable label and a value.
    pid = next(s for s in ann if s["segment"] == "PID")
    assert any(name == "Patient Name" for _no, name, _val in pid["fields"])


def test_generator_is_deterministic():
    assert make_adt(seed=7) == make_adt(seed=7)
    assert make_oru(seed=7) == make_oru(seed=7)

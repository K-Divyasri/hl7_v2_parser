"""Command-line HL7 parser: read a .hl7 file, print structured JSON.

    python parse_message.py --input data/sample/adt_a01.hl7
    python parse_message.py --input data/sample/oru_r01.hl7 --annotate

--annotate prints the labelled, field-by-field breakdown instead of the extracted
structure - handy for actually seeing what each segment holds.
"""
from __future__ import annotations

import argparse
import json
import sys

from hl7lib import parse, parse_message, annotate, HL7ParseError


def main(argv=None):
    ap = argparse.ArgumentParser(description="Parse an HL7 v2 message to JSON.")
    ap.add_argument("--input", required=True, help="Path to a .hl7 file.")
    ap.add_argument("--annotate", action="store_true",
                    help="Show the labelled segment/field breakdown.")
    args = ap.parse_args(argv)

    raw = open(args.input, "r", encoding="utf-8", newline="").read()

    try:
        if args.annotate:
            result = annotate(parse(raw))
        else:
            result = parse_message(raw)
    except HL7ParseError as e:
        # Plain ASCII - Windows consoles mangle fancy punctuation.
        print(f"Could not parse message: {e}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

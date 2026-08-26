"""Write the sample HL7 messages this project ships with.

    python generate_samples.py

Creates data/sample/adt_a01.hl7, data/sample/oru_r01.hl7, and a small batch/ of
mixed messages. Re-running is deterministic (seeded).
"""
from __future__ import annotations

from pathlib import Path

from hl7lib import write_samples, parse_message


def main():
    out = Path(__file__).parent / "data" / "sample"
    write_samples(out)
    print(f"Wrote sample messages to {out}")

    # Prove they parse, as a quick sanity check.
    adt = open(out / "adt_a01.hl7", encoding="utf-8", newline="").read()
    oru = open(out / "oru_r01.hl7", encoding="utf-8", newline="").read()
    a = parse_message(adt)
    o = parse_message(oru)
    print(f"ADT patient: {a['patient']['name']['given']} {a['patient']['name']['family']} "
          f"(class {a['visit']['patient_class']})")
    print(f"ORU results: {sum(len(ord_['observations']) for ord_ in o['orders'])} observations")
    print("Reminder: synthetic data only. Never put real patient data in a repo.")


if __name__ == "__main__":
    main()

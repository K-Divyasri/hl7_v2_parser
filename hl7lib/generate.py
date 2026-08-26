"""Generate synthetic HL7 v2 messages to practise on.

Real HL7 messages contain real patient data, so we make our own. These are fake
(Faker-generated) but structurally faithful ADT^A01 and ORU^R01 messages, with the
right segments and delimiters, so the parser has something real-shaped to chew on.

Synthetic data only - the whole point of Project 1's lesson.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from pathlib import Path

from faker import Faker

# A small lab panel for ORU messages: (LOINC, label, units, low, high).
LAB_PANEL = [
    ("2345-7", "Glucose", "mg/dL", 70, 99),
    ("2951-2", "Sodium", "mmol/L", 136, 145),
    ("2823-3", "Potassium", "mmol/L", 3.5, 5.1),
    ("718-7", "Hemoglobin", "g/dL", 12.0, 17.5),
    ("6690-2", "Leukocytes", "10*3/uL", 4.5, 11.0),
]


def _segment(name: str, fields: dict) -> str:
    """Build a non-MSH segment. `fields` maps 1-based field number -> value."""
    maxf = max(fields) if fields else 0
    parts = [name] + [str(fields.get(i, "")) for i in range(1, maxf + 1)]
    return "|".join(parts)


def _msh(fields: dict) -> str:
    """Build the MSH segment. MSH-1 (|) and MSH-2 (^~\\&) are fixed; `fields` maps
    field numbers 3+ to values."""
    maxf = max(fields)
    rest = [str(fields.get(i, "")) for i in range(3, maxf + 1)]
    return "MSH|^~\\&|" + "|".join(rest)


def _ts(dt: datetime) -> str:
    return dt.strftime("%Y%m%d%H%M%S")


# A fixed reference date so a patient's date of birth is reproducible. Faker's own
# date_of_birth() is measured from *today*, which would make the same seed produce
# a slightly different DOB tomorrow - the classic "don't call date.today() inside a
# generator" trap. We compute DOB from a fixed anchor instead.
_DOB_REFERENCE = date(2026, 1, 1)


def _patient(rng: random.Random, fake: Faker) -> dict:
    sex = rng.choice(["M", "F"])
    first = fake.first_name_male() if sex == "M" else fake.first_name_female()
    age = rng.randint(1, 95)
    dob = _DOB_REFERENCE - timedelta(days=age * 365 + rng.randint(0, 364))
    return {
        "mrn": f"MRN{rng.randint(100000, 999999)}",
        "first": first, "last": fake.last_name(), "middle": fake.first_name()[0],
        "sex": sex, "dob": dob.strftime("%Y%m%d"),
        "street": fake.street_address().replace("\n", " "),
        "city": fake.city(), "state": fake.state_abbr(), "zip": fake.zipcode(),
        "phone": fake.numerify("(###)###-####"), "ssn": fake.ssn(),
        "acct": f"ACC{rng.randint(100000, 999999)}",
    }


def make_adt(seed=0, event="A01") -> str:
    """Build an ADT^<event> message (default A01 = admit)."""
    rng = random.Random(seed)
    Faker.seed(seed)
    fake = Faker("en_US")
    p = _patient(rng, fake)
    when = datetime(2024, 1, 1) + timedelta(days=rng.randint(0, 600),
                                            hours=rng.randint(0, 23),
                                            minutes=rng.randint(0, 59))
    ctrl = f"MSG{rng.randint(10000, 99999)}"

    msh = _msh({3: "ADT_APP", 4: "MERCY_GENERAL", 5: "EHR", 6: "MERCY_GENERAL",
                7: _ts(when), 9: f"ADT^{event}", 10: ctrl, 11: "P", 12: "2.5.1"})
    evn = _segment("EVN", {1: event, 2: _ts(when)})
    pid = _segment("PID", {
        1: "1", 3: f"{p['mrn']}^^^MERCY^MR",
        5: f"{p['last']}^{p['first']}^{p['middle']}",
        7: p["dob"], 8: p["sex"],
        11: f"{p['street']}^^{p['city']}^{p['state']}^{p['zip']}",
        13: p["phone"], 16: rng.choice(["M", "S"]), 18: p["acct"], 19: p["ssn"],
    })
    kin_last = fake.last_name()
    nk1 = _segment("NK1", {1: "1", 2: f"{kin_last}^{fake.first_name()}",
                           3: rng.choice(["SPO", "CHD", "PAR"])})
    doc_last, doc_first = fake.last_name(), fake.first_name()
    pv1 = _segment("PV1", {
        1: "1", 2: rng.choice(["I", "O", "E"]),
        3: f"{rng.choice(['ICU', '3W', 'ER'])}^{rng.randint(100, 499)}^A",
        7: f"{rng.randint(1000, 9999)}^{doc_last}^{doc_first}",
        10: rng.choice(["MED", "SUR", "CAR"]),
        19: f"VN{rng.randint(100000, 999999)}", 44: _ts(when),
    })
    return "\r".join([msh, evn, pid, nk1, pv1])


def make_oru(seed=0) -> str:
    """Build an ORU^R01 lab-result message with a panel of OBX results."""
    rng = random.Random(seed + 9000)  # offset so ADT/ORU with same seed differ
    Faker.seed(seed + 9000)
    fake = Faker("en_US")
    p = _patient(rng, fake)
    collected = datetime(2024, 1, 1) + timedelta(days=rng.randint(0, 600))
    reported = collected + timedelta(hours=rng.randint(1, 6))
    ctrl = f"MSG{rng.randint(10000, 99999)}"

    msh = _msh({3: "LAB", 4: "MERCY_LAB", 5: "EHR", 6: "MERCY_GENERAL",
                7: _ts(reported), 9: "ORU^R01", 10: ctrl, 11: "P", 12: "2.5.1"})
    pid = _segment("PID", {
        1: "1", 3: f"{p['mrn']}^^^MERCY^MR",
        5: f"{p['last']}^{p['first']}^{p['middle']}", 7: p["dob"], 8: p["sex"],
    })
    obr = _segment("OBR", {
        1: "1", 2: f"ORD{rng.randint(10000, 99999)}",
        3: f"FIL{rng.randint(10000, 99999)}",
        4: "24323-8^Comprehensive metabolic panel^LN",
        7: _ts(collected), 25: "F",
    })
    segments = [msh, pid, obr]
    for i, (code, label, units, low, high) in enumerate(LAB_PANEL, start=1):
        # Mostly normal, sometimes out of range, so abnormal flags appear.
        if rng.random() < 0.25:
            value = round(rng.uniform(high, high * 1.4), 1)
            flag = "H"
        elif rng.random() < 0.2:
            value = round(rng.uniform(low * 0.6, low), 1)
            flag = "L"
        else:
            value = round(rng.uniform(low, high), 1)
            flag = "N"
        segments.append(_segment("OBX", {
            1: str(i), 2: "NM", 3: f"{code}^{label}^LN", 5: value, 6: units,
            7: f"{low}-{high}", 8: flag, 11: "F",
        }))
    return "\r".join(segments)


def write_samples(out_dir, n_batch=6) -> Path:
    """Write a couple of headline samples plus a small batch folder."""
    out = Path(out_dir)
    (out / "batch").mkdir(parents=True, exist_ok=True)

    def _write(path, text):
        # newline="" so the \r segment terminators are preserved exactly.
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(text)

    _write(out / "adt_a01.hl7", make_adt(seed=1))
    _write(out / "oru_r01.hl7", make_oru(seed=1))
    for i in range(n_batch):
        kind = make_adt(seed=100 + i) if i % 2 == 0 else make_oru(seed=100 + i)
        name = "adt" if i % 2 == 0 else "oru"
        _write(out / "batch" / f"{name}_{i:02d}.hl7", kind)
    return out

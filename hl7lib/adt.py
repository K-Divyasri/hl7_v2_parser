"""Extract structured data from an ADT message (admit / discharge / transfer).

ADT messages keep registration, billing, and clinical systems in sync as a
patient moves through the hospital. A01 = admit, A03 = discharge, A08 = update,
and so on - the trigger event is the second component of MSH-9 (e.g. ADT^A01).

We pull the three things that matter: who sent it (MSH), who the patient is (PID),
and the visit (PV1). The shared MSH and PID readers live here and are reused by
the ORU extractor too.
"""
from __future__ import annotations

from .parser import parse, Message


def _as_message(m) -> Message:
    return m if isinstance(m, Message) else parse(m)


def read_msh(m: Message) -> dict:
    return {
        "message_type": m.get("MSH", 9, comp=1),
        "trigger_event": m.get("MSH", 9, comp=2),
        "control_id": m.get("MSH", 10),
        "sending_application": m.get("MSH", 3),
        "sending_facility": m.get("MSH", 4),
        "receiving_application": m.get("MSH", 5),
        "receiving_facility": m.get("MSH", 6),
        "timestamp": m.get("MSH", 7),
        "version": m.get("MSH", 12),
    }


def read_pid(m: Message) -> dict:
    return {
        "patient_id": m.get("PID", 3, comp=1),
        "name": {
            "family": m.get("PID", 5, comp=1),
            "given": m.get("PID", 5, comp=2),
            "middle": m.get("PID", 5, comp=3),
        },
        "date_of_birth": m.get("PID", 7),
        "sex": m.get("PID", 8),
        # PID-10 (race) is CE-coded: identifier^text^system. Prefer the text.
        "race": m.get("PID", 10, comp=2) or m.get("PID", 10, comp=1),
        "address": {
            "street": m.get("PID", 11, comp=1),
            "city": m.get("PID", 11, comp=3),
            "state": m.get("PID", 11, comp=4),
            "zip": m.get("PID", 11, comp=5),
        },
        "phone": m.get("PID", 13, comp=1),
        "ssn": m.get("PID", 19),
    }


def read_pv1(m: Message) -> dict:
    return {
        "patient_class": m.get("PV1", 2),
        "location": {
            "point_of_care": m.get("PV1", 3, comp=1),
            "room": m.get("PV1", 3, comp=2),
            "bed": m.get("PV1", 3, comp=3),
        },
        "attending_doctor": {
            "id": m.get("PV1", 7, comp=1),
            "family": m.get("PV1", 7, comp=2),
            "given": m.get("PV1", 7, comp=3),
        },
        "hospital_service": m.get("PV1", 10),
        "visit_number": m.get("PV1", 19, comp=1),
        "admit_date": m.get("PV1", 44),
        "discharge_date": m.get("PV1", 45),
    }


def parse_adt(message) -> dict:
    """Turn an ADT message (raw string or Message) into a structured dict."""
    m = _as_message(message)
    return {
        "message": read_msh(m),
        "event": {
            "type_code": m.get("EVN", 1) or m.get("MSH", 9, comp=2),
            "recorded_at": m.get("EVN", 2),
        },
        "patient": read_pid(m),
        "visit": read_pv1(m),
    }

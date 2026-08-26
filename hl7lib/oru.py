"""Extract structured data from an ORU message (observation result, e.g. labs).

An ORU^R01 carries results back from a lab or device to the ordering system. Its
shape is: MSH, PID, [PV1], then one or more OBR (the order / panel) each followed
by a run of OBX segments (the individual results). A complete blood count, for
example, is one OBR with an OBX per analyte (white cells, hemoglobin, ...).

The interesting bit is the grouping: each OBX belongs to the OBR above it. We walk
the segments in order and attach observations to the current order.
"""
from __future__ import annotations

from .parser import parse, Message
from .adt import read_msh, read_pid


def _as_message(m) -> Message:
    return m if isinstance(m, Message) else parse(m)


def _read_obx(seg) -> dict:
    return {
        "set_id": seg.get(1),
        "value_type": seg.get(2),                 # NM=numeric, ST=string, TX=text
        "code": seg.get(3, comp=1),               # e.g. LOINC code
        "label": seg.get(3, comp=2),
        "code_system": seg.get(3, comp=3),         # e.g. LN for LOINC
        "value": seg.get(5),
        "units": seg.get(6, comp=1),
        "reference_range": seg.get(7),
        "abnormal_flag": seg.get(8),               # H=high, L=low, N=normal
        "status": seg.get(11),                     # F=final, P=preliminary
    }


def _read_obr(seg) -> dict:
    return {
        "placer_order_number": seg.get(2, comp=1),
        "filler_order_number": seg.get(3, comp=1),
        "service": {"code": seg.get(4, comp=1), "text": seg.get(4, comp=2)},
        "observation_datetime": seg.get(7),
        "result_status": seg.get(25),
    }


def parse_oru(message) -> dict:
    """Turn an ORU message (raw string or Message) into a structured dict with
    orders, each holding its own list of observations."""
    m = _as_message(message)

    orders = []
    current = None
    for seg in m.segments:
        if seg.name == "OBR":
            current = _read_obr(seg)
            current["observations"] = []
            orders.append(current)
        elif seg.name == "OBX":
            if current is None:
                # OBX before any OBR - still capture it under a placeholder order.
                current = {"service": {"code": "", "text": ""}, "observations": []}
                orders.append(current)
            current["observations"].append(_read_obx(seg))

    return {
        "message": read_msh(m),
        "patient": read_pid(m),
        "orders": orders,
    }

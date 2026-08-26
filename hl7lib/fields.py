"""Human-readable names for the common HL7 segments and fields.

HL7 fields are referred to by number (PID-5, OBX-3), which is precise but opaque
until you've memorised them. These maps turn a parsed segment into a labelled,
readable dump - exactly the "explain each segment" deliverable Project 3 asks for,
and a great teaching aid in the notebooks.

The names follow the HL7 v2.5.1 standard. We only cover the fields these messages
actually use; the real standard has many more.
"""
from __future__ import annotations

SEGMENT_NAMES = {
    "MSH": "Message Header",
    "EVN": "Event Type",
    "PID": "Patient Identification",
    "NK1": "Next of Kin / Associated Parties",
    "PV1": "Patient Visit",
    "OBR": "Observation Request",
    "OBX": "Observation / Result",
    "AL1": "Patient Allergy Information",
    "DG1": "Diagnosis",
}

FIELD_NAMES = {
    "MSH": {
        1: "Field Separator", 2: "Encoding Characters", 3: "Sending Application",
        4: "Sending Facility", 5: "Receiving Application", 6: "Receiving Facility",
        7: "Date/Time of Message", 9: "Message Type", 10: "Message Control ID",
        11: "Processing ID", 12: "Version ID",
    },
    "EVN": {1: "Event Type Code", 2: "Recorded Date/Time", 6: "Event Occurred"},
    "PID": {
        1: "Set ID", 3: "Patient Identifier List", 5: "Patient Name",
        7: "Date/Time of Birth", 8: "Administrative Sex", 10: "Race",
        11: "Patient Address", 13: "Phone Number - Home", 16: "Marital Status",
        19: "SSN Number",
    },
    "NK1": {1: "Set ID", 2: "Name", 3: "Relationship", 4: "Address", 5: "Phone"},
    "PV1": {
        1: "Set ID", 2: "Patient Class", 3: "Assigned Patient Location",
        7: "Attending Doctor", 10: "Hospital Service", 19: "Visit Number",
        44: "Admit Date/Time", 45: "Discharge Date/Time",
    },
    "OBR": {
        1: "Set ID", 2: "Placer Order Number", 3: "Filler Order Number",
        4: "Universal Service Identifier", 7: "Observation Date/Time",
        25: "Result Status",
    },
    "OBX": {
        1: "Set ID", 2: "Value Type", 3: "Observation Identifier",
        5: "Observation Value", 6: "Units", 7: "References Range",
        8: "Abnormal Flags", 11: "Observation Result Status",
        14: "Date/Time of the Observation",
    },
    "AL1": {1: "Set ID", 3: "Allergen Code", 4: "Severity", 5: "Reaction"},
    "DG1": {1: "Set ID", 3: "Diagnosis Code", 4: "Diagnosis Description"},
}


def describe_segment(seg):
    """Return [(field_no, field_name, raw_value), ...] for the non-empty fields of
    a segment, using the human-readable names where we know them."""
    names = FIELD_NAMES.get(seg.name, {})
    rows = []
    for i in range(1, len(seg.fields) + 1):
        value = seg.field(i)
        if value == "":
            continue
        label = names.get(i, f"{seg.name}-{i}")
        rows.append((i, label, value))
    return rows


def annotate(message):
    """Annotated view of a whole message: a list of {segment, name, fields}."""
    out = []
    for seg in message.segments:
        out.append({
            "segment": seg.name,
            "name": SEGMENT_NAMES.get(seg.name, "Unknown segment"),
            "fields": describe_segment(seg),
        })
    return out

# HL7 v2 parser - a "paste a message, get structured JSON" web app.
#
# This is a thin Streamlit wrapper around the real parser you built in
# build_from_scratch/hl7lib. Streamlit turns a plain Python script into a small web
# page: every st.something() call draws a widget. There is no HTML or JavaScript to
# write. When someone changes an input or clicks a button, Streamlit re-runs this
# whole file top to bottom and redraws the page - keep that in mind as you read.

import pathlib
import sys

# --- Make the real parser importable -----------------------------------------
# This file lives at hosting/streamlit_app/app.py. The parser package (hl7lib) lives
# at build_from_scratch/hl7lib. So we climb two folders up from this file
# (streamlit_app -> hosting -> project root) and step into build_from_scratch, then
# add that to Python's import path. After this line, "import hl7lib" just works.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "build_from_scratch"))

import streamlit as st

# These are the exact names your hl7lib package exports (see hl7lib/__init__.py):
#   parse          - raw text  -> a Message object (segments + delimiters)
#   parse_message  - raw text  -> a structured dict (dispatches ADT / ORU / other)
#   annotate       - a Message -> a labelled, field-by-field breakdown
#   make_adt/oru   - build a synthetic sample message to try things on
#   HL7ParseError  - raised when the input is not a sane HL7 message
from hl7lib import parse, parse_message, annotate, make_adt, make_oru, HL7ParseError


# --- Page setup --------------------------------------------------------------
st.set_page_config(page_title="HL7 v2 parser", page_icon="🧬", layout="wide")

st.title("HL7 v2 message parser")
st.write(
    "Paste an HL7 v2 message (or load a sample) and this parses it into structured "
    "JSON plus a labelled, field-by-field breakdown. It handles ADT (admit / "
    "discharge / transfer) and ORU (lab results)."
)

# The one rule that matters most in health tech. Keep it loud and unmissable.
st.warning(
    "Synthetic data only - never paste real patient data (PHI) into a public app. "
    "This demo is public. Use the sample buttons, or messages you know are fake.",
    icon="⚠️",
)


# --- The message text box ----------------------------------------------------
# We keep the current message text in st.session_state so the "Load sample" buttons
# can fill the box. session_state is Streamlit's memory that survives a re-run.
if "message_text" not in st.session_state:
    st.session_state["message_text"] = ""

# HL7's real segment terminator is a carriage return (\r), which a text box can't
# show as separate lines. So samples are displayed with normal newlines (\n) between
# segments for readability; we convert back to \r just before parsing (below).
col_adt, col_oru = st.columns(2)
with col_adt:
    if st.button("Load sample ADT", use_container_width=True):
        st.session_state["message_text"] = make_adt(1).replace("\r", "\n")
with col_oru:
    if st.button("Load sample ORU", use_container_width=True):
        st.session_state["message_text"] = make_oru(1).replace("\r", "\n")

st.text_area(
    "HL7 message",
    key="message_text",   # ties the box to session_state["message_text"]
    height=220,
    placeholder="MSH|^~\\&|ADT_APP|MERCY_GENERAL|EHR|...\nEVN|A01|...\nPID|1||...",
    help="One segment per line. The buttons above load a fake sample you can edit.",
)

parse_clicked = st.button("Parse message", type="primary")


# --- Parse and show the results ----------------------------------------------
if parse_clicked:
    # The text box gives us newline-separated segments. The parser tolerates \n, but
    # we are explicit and convert to \r - the true HL7 segment terminator - so the
    # app behaves exactly like a real feed reading off the wire.
    raw = st.session_state["message_text"].replace("\r\n", "\n").replace("\n", "\r")

    if not raw.strip():
        st.info("Nothing to parse yet. Load a sample or paste a message above.")
    else:
        try:
            # Two views of the same message:
            #   structured = the clean nested dict (patient, visit, orders, ...)
            #   message    = the Message object, which annotate() labels field by field
            structured = parse_message(raw)
            message = parse(raw)
        except HL7ParseError as err:
            # Bad input lands here instead of crashing the app. Show a friendly hint.
            st.error(
                f"That does not look like a valid HL7 v2 message: {err}\n\n"
                "A message must start with an MSH segment, e.g. "
                "'MSH|^~\\&|...'. Try a sample button to see the shape.",
                icon="🚫",
            )
        else:
            st.success("Parsed successfully.")

            left, right = st.columns(2)

            # (a) The structured JSON - what your extractors pulled out.
            with left:
                st.subheader("Structured JSON")
                st.caption("The clean, nested data your ADT/ORU extractors produced.")
                st.json(structured)

            # (b) The annotated, field-by-field breakdown - one table per segment.
            with right:
                st.subheader("Field-by-field breakdown")
                st.caption("Every non-empty field, with its HL7 name and raw value.")
                # annotate() returns a list of segments, each:
                #   {"segment": "PID", "name": "Patient Identification",
                #    "fields": [(5, "Patient Name", "Scott^Chad^T"), ...]}
                for seg in annotate(message):
                    st.markdown(f"**{seg['segment']}** - {seg['name']}")
                    # st.table wants simple rows; a list of dicts renders as columns.
                    rows = [
                        {
                            "Field": f"{seg['segment']}-{field_no}",
                            "Name": field_name,
                            "Value": value,
                        }
                        for field_no, field_name, value in seg["fields"]
                    ]
                    if rows:
                        st.table(rows)
                    else:
                        st.caption("(no fields)")


# --- Footer ------------------------------------------------------------------
st.divider()
st.caption(
    "Built on hl7lib, a from-scratch HL7 v2 parser (pure standard-library Python). "
    "Samples are generated with Faker. Project 3 of a health-tech learning roadmap."
)

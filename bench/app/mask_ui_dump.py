#!/usr/bin/env python3
# Masks a UI hierarchy dump (Appium GET /session/<id>/source) before it is written to disk.
# Run by bench/app/run_appium.sh on a failed step d. Usage: python3 -I mask_ui_dump.py <source.json> <out.xml>
# Exit codes: 0 written; 2 input or secret problem (nothing written); 3 a secret value was still found after
# masking (nothing written). Nothing is printed except the exit reason, never a screen text or a secret.
#
# Secret values come from the environment only:
#   BENCH_TEST_EMAIL, BENCH_TEST_EMAIL_PASSWORD, BENCH_BOARD_POP (the setup code, typed into the connect step),
#   BENCH_WIFI_PASSWORD. Each must be set and at least 4 characters, or the dump is not written (fail closed).
# Rules, applied in this order:
#   1. text, content-desc and hint of every input field (class contains EditText, or password="true") are blanked.
#   2. every known secret value is replaced in every attribute (upper and lower case too).
#   3. a percentage reading ("42 %") is replaced, so no soil-moisture value is written.
#   4. the result is checked again; if a secret value (plain or XML-escaped) is still present, nothing is written.
# A device token is not on screen and has no environment variable here; it is not in the list above.
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

SECRET_ENV = ["BENCH_TEST_EMAIL", "BENCH_TEST_EMAIL_PASSWORD", "BENCH_BOARD_POP", "BENCH_WIFI_PASSWORD"]
MASK = "[masked]"
READING = re.compile(r"\d+(?:[.,]\d+)?\s*%")
READING_MASK = "[reading masked]"
INPUT_ATTRS = ("text", "content-desc", "hint")


def fail(code, why):
    sys.stderr.write("mask_ui_dump: " + why + " (no dump written)\n")
    sys.exit(code)


def secret_values():
    vals = set()
    for name in SECRET_ENV:
        v = os.environ.get(name, "")
        if not v:
            fail(2, "secret " + name + " is not set, so the dump cannot be masked")
        if len(v) < 4:
            fail(2, "secret " + name + " is too short to mask safely")
        if "\n" in v or "\r" in v:
            fail(2, "secret " + name + " has a line break")
        vals.add(v)
        vals.add(v.upper())
        vals.add(v.lower())
    return sorted(vals, key=len, reverse=True)


def main():
    if len(sys.argv) != 3:
        fail(2, "usage: mask_ui_dump.py <source.json> <out.xml>")
    src, out = sys.argv[1], sys.argv[2]
    secrets = secret_values()
    try:
        with open(src, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        fail(2, "page source file is missing or not JSON")
    xml_text = data.get("value") if isinstance(data, dict) else None
    if not isinstance(xml_text, str) or not xml_text.strip():
        fail(2, "page source has no XML text")
    try:
        root = ET.fromstring(xml_text.encode("utf-8"))
    except ET.ParseError:
        fail(2, "page source is not well-formed XML")

    for elem in root.iter():
        attrs = elem.attrib
        is_input = "EditText" in attrs.get("class", "") or attrs.get("password") == "true"
        if is_input:
            for key in INPUT_ATTRS:
                if attrs.get(key):
                    attrs[key] = MASK
        for key, val in list(attrs.items()):
            new = val
            for s in secrets:
                new = new.replace(s, MASK)
            attrs[key] = READING.sub(READING_MASK, new)

    # Check again on the parsed values and on the escaped text as it would be written.
    body = ET.tostring(root, encoding="unicode")
    needles = set()
    for s in secrets:
        needles.add(s)
        needles.add(escape(s))
        needles.add(escape(s, {'"': "&quot;"}))
    for elem in root.iter():
        for val in elem.attrib.values():
            if any(n in val for n in needles):
                fail(3, "a secret value is still present after masking")
    if any(n in body for n in needles):
        fail(3, "a secret value is still present after masking")

    text = '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"
    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text)
    sys.stderr.write("mask_ui_dump: written, secrets and readings masked\n")


if __name__ == "__main__":
    main()

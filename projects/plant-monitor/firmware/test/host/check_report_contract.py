#!/usr/bin/env python3
"""Task 4.F3 drift check: the hourly report built by the firmware (nw_report_build) must
  (a) validate against docs/interfaces/device-report.schema.json (the ingest contract, FR-D02, openapi.yaml /ingest), and
  (b) equal docs/interfaces/fixtures/device-report.valid.json (same values, same field names).
A small built-in validator covers the keywords this schema uses (no jsonschema package needed on CI).
Negative cases check that the validator rejects bad payloads, so (a) is not vacuous.
Usage: check_report_contract.py <path to test_report binary>"""
import copy, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
IFACE = os.path.join(HERE, "..", "..", "..", "docs", "interfaces")
SCHEMA = os.path.join(IFACE, "device-report.schema.json")
FIXTURE = os.path.join(IFACE, "fixtures", "device-report.valid.json")

fails = []


def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


def _is_type(v, t):
    if t == "null":
        return v is None
    if t == "boolean":
        return isinstance(v, bool)
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == "string":
        return isinstance(v, str)
    if t == "array":
        return isinstance(v, list)
    if t == "object":
        return isinstance(v, dict)
    raise ValueError("unsupported type " + t)


def validate(value, schema, path="$"):
    """Returns a list of error strings (empty = valid). Supports the keywords used by device-report.schema.json."""
    errs = []
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(_is_type(value, t) for t in types):
            return [f"{path}: type {types} expected, got {type(value).__name__}"]
    if "const" in schema and value != schema["const"]:
        errs.append(f"{path}: const {schema['const']!r} expected")
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} not in enum {schema['enum']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errs.append(f"{path}: {value} < minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            errs.append(f"{path}: {value} > maximum {schema['maximum']}")
    if isinstance(value, str) and "maxLength" in schema and len(value) > schema["maxLength"]:
        errs.append(f"{path}: longer than maxLength {schema['maxLength']}")
    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errs.append(f"{path}: fewer than minItems {schema['minItems']}")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errs.append(f"{path}: more than maxItems {schema['maxItems']} ({len(value)})")
        if "items" in schema:
            for i, item in enumerate(value):
                errs += validate(item, schema["items"], f"{path}[{i}]")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for req in schema.get("required", []):
            if req not in value:
                errs.append(f"{path}: missing required '{req}'")
        if schema.get("additionalProperties") is False:
            for k in value:
                if k not in props:
                    errs.append(f"{path}: unknown property '{k}'")
        for k, sub in props.items():
            if k in value:
                errs += validate(value[k], sub, f"{path}.{k}")
    return errs


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    binary = os.path.abspath(sys.argv[1])
    schema = json.load(open(SCHEMA, encoding="utf-8"))
    fixture = json.load(open(FIXTURE, encoding="utf-8"))

    # (0) the fixture itself is valid (guards the checker)
    errs = validate(fixture, schema)
    check(not errs, f"cloud fixture device-report.valid.json validates against the schema {errs[:3]}")

    # (a) and (b): firmware output
    with tempfile.TemporaryDirectory() as d:
        out_path = os.path.join(d, "hourly.json")
        res = subprocess.run([binary, out_path], capture_output=True, text=True)
        check(res.returncode == 0, "test_report exits 0 (all unit checks pass)")
        if res.returncode != 0:
            print(res.stdout)
        check(os.path.exists(out_path), "test_report wrote the hourly payload")
        payload = json.load(open(out_path, encoding="utf-8")) if os.path.exists(out_path) else {}
    errs = validate(payload, schema)
    check(not errs, f"firmware payload validates against device-report.schema.json {errs[:3]}")
    check(payload == fixture, "firmware payload equals docs/interfaces/fixtures/device-report.valid.json (field by field)")
    check("ota" not in payload and "cal" not in payload, "no ota and no cal in this payload (OTA out of scope; cal NULL in test)")

    # negative cases: the validator must reject each one
    neg = {
        "extra property": lambda p: p.update({"rssi": -60}),
        "193 samples (maxItems 192)": lambda p: p.update({"samples": p["samples"] * 49}),
        "sample ts before 2023 (minimum)": lambda p: p["samples"][0].update({"ts": 12345}),
        "temp_c sent as a string": lambda p: p["samples"][0].update({"temp_c": "21.4"}),
        "trigger outside enum": lambda p: p.update({"trigger": "hourly"}),
        "forecast above 72 h": lambda p: p.update({"forecast_h": 72.5}),
        "missing samples": lambda p: p.pop("samples"),
        "v != 1": lambda p: p.update({"v": 2}),
    }
    for name, mutate in neg.items():
        bad = copy.deepcopy(fixture)
        mutate(bad)
        check(bool(validate(bad, schema)), f"validator rejects: {name}")
    # control: x-plausible ranges are documented as NOT enforced by the schema (server stores plausible=false instead)
    ctrl = copy.deepcopy(fixture)
    ctrl["samples"][0]["moisture_pct"] = 101.0
    check(not validate(ctrl, schema), "control: moisture 101 % is a schema-valid value (x-plausible, server flags it)")

    print("")
    if fails:
        print(f"{len(fails)} contract check(s) FAILED")
        return 1
    print("all contract checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

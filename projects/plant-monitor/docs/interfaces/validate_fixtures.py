#!/usr/bin/env python3
"""Validate the /ingest report fixtures against device-report.schema.json (task 2.4).
fixtures/device-report*.json must be valid; fixtures/invalid/*.json must be rejected.
Usage: python3 validate_fixtures.py   (needs: pip install jsonschema). Exit 1 on any surprise."""
import glob, json, os, sys
from jsonschema import Draft202012Validator

here = os.path.dirname(os.path.abspath(__file__))
schema = json.load(open(os.path.join(here, "device-report.schema.json")))
Draft202012Validator.check_schema(schema)
v = Draft202012Validator(schema)
ok = True
for f in sorted(glob.glob(os.path.join(here, "fixtures", "device-report*.json"))):
    errs = list(v.iter_errors(json.load(open(f))))
    print(("FAIL (should be valid) " if errs else "ok   valid   ") + os.path.relpath(f, here))
    ok &= not errs
for f in sorted(glob.glob(os.path.join(here, "fixtures", "invalid", "*.json"))):
    errs = list(v.iter_errors(json.load(open(f))))
    print(("ok   invalid " if errs else "FAIL (should be rejected) ") + os.path.relpath(f, here))
    ok &= bool(errs)
sys.exit(0 if ok else 1)

#!/usr/bin/env python3
"""PLANT_API_BASE_URL is a build setting and must not be committed (A-082, task 4.F1 v1 bench).
Fails when: Kconfig default is not the placeholder https://api.invalid; any git-tracked-looking firmware file sets
CONFIG_PLANT_API_BASE_URL to something else; sdkconfig.defaults.local is not git-ignored; the doc does not describe the setting.
`--selftest` proves each rule can fail."""
import re, sys, pathlib

root = pathlib.Path(__file__).resolve().parents[2]
repo = root.parents[2]
PLACEHOLDER = "https://api.invalid"
SKIP = {"build", "build-host", "sdkconfig", "sdkconfig.old", "sdkconfig.defaults.local"}

def check(files, kconfig, gitignore, doc):
    errors = []
    m = re.search(r'config PLANT_API_BASE_URL\s+string[^\n]*\n\s+default "([^"]*)"', kconfig)
    if not m or m.group(1) != PLACEHOLDER: errors.append(f"Kconfig default for PLANT_API_BASE_URL is not {PLACEHOLDER}")
    for name, text in files.items():
        for v in re.findall(r'CONFIG_PLANT_API_BASE_URL\s*=\s*"?([^"\n]*)"?', text):
            if v != PLACEHOLDER: errors.append(f"{name} sets CONFIG_PLANT_API_BASE_URL={v}: real URLs are never committed")
    if "sdkconfig.defaults.local" not in gitignore: errors.append(".gitignore does not list sdkconfig.defaults.local")
    if "PLANT_API_BASE_URL" not in doc or "not committed" not in doc.lower(): errors.append("FIRMWARE-BENCH.md does not document PLANT_API_BASE_URL as a build setting, not committed")
    return errors

def main():
    files = {}
    for p in root.rglob("*"):
        if p.is_file() and not (set(p.relative_to(root).parts) & SKIP) and p.suffix in ("", ".defaults", ".v1", ".txt", ".projbuild", ".h", ".c", ".md", ".cmake", ".yml"):
            try: files[str(p.relative_to(repo))] = p.read_text()
            except UnicodeDecodeError: pass
    kc = (root / "main" / "Kconfig.projbuild").read_text()
    gi = (repo / ".gitignore").read_text()
    doc = (root.parent / "v1" / "FIRMWARE-BENCH.md").read_text()
    if "--selftest" in sys.argv:
        bad = 0
        cases = [("real url in a defaults file", ({**files, "x/sdkconfig.defaults.v1": 'CONFIG_PLANT_API_BASE_URL="https://abc.supabase.co/functions/v1"\n'}, kc, gi, doc)),
                 ("kconfig default changed", (files, kc.replace(PLACEHOLDER, "https://abc.example"), gi, doc)),
                 ("local file not ignored", (files, kc, gi.replace("sdkconfig.defaults.local", ""), doc)),
                 ("doc missing", (files, kc, gi, ""))]
        for label, args in cases:
            if check(*args): print(f"ok  mutant caught: {label}")
            else: print(f"FAIL mutant survived: {label}"); bad += 1
        if check(files, kc, gi, doc): print("FAIL unmutated input does not pass"); bad += 1
        sys.exit(1 if bad else 0)
    errors = check(files, kc, gi, doc)
    if errors: print("\n".join("FAIL " + e for e in errors)); sys.exit(1)
    print(f"ok  scanned {len(files)} firmware files, no real API URL; default {PLACEHOLDER}; local file ignored; documented")

main()

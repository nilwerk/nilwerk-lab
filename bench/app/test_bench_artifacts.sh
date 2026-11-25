#!/usr/bin/env bash
# Offline test for the bench artifacts in .github/workflows/bench.yml (UI dump on failure, serial log always, redaction check).
# Needs bash and python3 only. No Pi, phone, board, Appium or GitHub call. Checks the workflow TEXT and the step order.
# It also runs the check on two broken copies, which must fail (so the check cannot pass by accident).
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../.." && pwd)"
wf="$repo/.github/workflows/bench.yml"
app="$here/run_appium.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

cat > "$tmp/check.py" <<'PY'
import re, sys
wf_path, app_path = sys.argv[1], sys.argv[2]
lines = open(wf_path, encoding="utf-8").read().split("\n")
errors = []

def need(cond, msg):
    if not cond:
        errors.append(msg)

# A step starts at a "      - name:" line and ends before the next step or job-level key.
starts = [i for i, l in enumerate(lines) if re.match(r"^      - name: ", l)]
blocks = {}
for n, s in enumerate(starts):
    end = len(lines)
    for j in range(s + 1, len(lines)):
        if re.match(r"^      - ", lines[j]) or re.match(r"^  \S", lines[j]):
            end = j
            break
    name = lines[s][len("      - name: "):].strip().strip('"')
    blocks[name] = (s, "\n".join(lines[s:end]))

def find(prefix):
    hits = [(k, v) for k, v in blocks.items() if k.startswith(prefix)]
    if len(hits) != 1:
        errors.append("expected exactly one step named '%s...', found %d" % (prefix, len(hits)))
        return None, ""
    return hits[0][1]

def index_of(prefix):
    hits = [v[0] for k, v in blocks.items() if k.startswith(prefix)]
    return hits[0] if len(hits) == 1 else None

# 1. UI dump upload: exists, only on failure, uploads the dump folder.
i, b = find("d+.")
need("upload-artifact@" in b, "d+ (UI dump upload): not an upload-artifact step")
need(re.search(r"^        if: failure\(\)\s*$", b, re.M) is not None, "d+ (UI dump upload): missing 'if: failure()'")
need("bench-ui-dump" in b, "d+ (UI dump upload): does not upload the bench-ui-dump folder")

# 2. Serial log upload: exists, always, uploads the serial log file.
i, b = find("s3+.")
need("upload-artifact@" in b, "s3+ (serial upload): not an upload-artifact step")
need(re.search(r"^        if: always\(\)\s*$", b, re.M) is not None, "s3+ (serial upload): missing 'if: always()'")
need("bench-serial/serial.log" in b, "s3+ (serial upload): does not upload bench-serial/serial.log")

# 3. Redaction check: exists, always, fails closed (deletes the log), greps for each known secret, reads all four names.
i3, b = find("s3.")
need(re.search(r"^        if: always\(\)\s*$", b, re.M) is not None, "s3 (redaction check): missing 'if: always()'")
need("grep -q -F -f" in b, "s3 (redaction check): no fixed-string grep of the secret values")
need('rm -f -- "$log"' in b, "s3 (redaction check): does not delete the log when the check fails (fail closed)")
need("exit 1" in b, "s3 (redaction check): no failing exit")
for name in ("BENCH_BOARD_POP", "BENCH_WIFI_PASSWORD", "BENCH_TEST_EMAIL_PASSWORD", "BENCH_CLOUD_CHECK_CONFIG"):
    need(("%s: ${{ secrets.%s }}" % (name, name)) in b, "s3 (redaction check): secret %s is not checked" % name)

# 4. Serial capture: start after step 3 and before c, stop before b, check before the upload, d2 reads the log.
i_3 = index_of("3. Provision")
i_s1 = index_of("s1.")
i_c = index_of("c. BLE")
i_s2 = index_of("s2.")
i_b = index_of("b. Serial live")
i_e2e = index_of("Bench E2E")
i_s3 = index_of("s3.")
i_s3p = index_of("s3+.")
i_d2 = index_of("d2.")
need(None not in (i_3, i_s1, i_c), "s1 (serial start): step order 3 -> s1 -> c not found")
if None not in (i_3, i_s1, i_c): need(i_3 < i_s1 < i_c, "s1 (serial start) must come after step 3 and before c")
need(i_s2 is not None and i_b is not None and i_s2 < i_b, "s2 (serial stop) must come before b")
need(i_s2 is not None and re.search(r"^        if: always\(\)\s*$", blocks[[k for k in blocks if k.startswith("s2.")][0]][1], re.M) is not None,
     "s2 (serial stop): missing 'if: always()'")
need(None not in (i_s3, i_s3p, i_e2e, i_d2), "s3, s3+ or d2 step missing")
if None not in (i_s3, i_s3p, i_e2e, i_d2):
    need(i_e2e < i_s3 < i_s3p < i_d2, "order must be E2E -> s3 -> s3+ -> d2")
i_d2_name, b2 = find("d2.")
need("BENCH_SETUP_LOG: ${{ runner.temp }}/bench-serial/serial.log" in b2, "d2 does not read the serial capture (BENCH_SETUP_LOG)")

# 5. Step d writes the dump folder; run_appium.sh writes it through the masker and keeps its failure hook.
_, bd = find("d. App flow")
need("BENCH_UI_DUMP_DIR: ${{ runner.temp }}/bench-ui-dump" in bd, "step d does not set BENCH_UI_DUMP_DIR")
try:
    app = open(app_path, encoding="utf-8").read()
except OSError:
    app = ""
need("dump_ui_on_failure" in app and "mask_ui_dump.py" in app, "run_appium.sh has no UI dump on failure through mask_ui_dump.py")

for e in errors:
    print("FAIL: " + e)
if errors:
    sys.exit(1)
print("bench artifacts check: all rules hold")
PY

fails=0
run_case() { # run_case <label> <expect 0|1> <workflow path>
  python3 -I "$tmp/check.py" "$3" "$app" > "$tmp/out.txt" 2>&1; rc=$?
  if { [ "$2" = "0" ] && [ "$rc" = "0" ]; } || { [ "$2" = "1" ] && [ "$rc" != "0" ]; }; then
    echo "ok: $1 (exit $rc)"
  else
    echo "FAIL: $1 (exit $rc, expected $2)"; cat "$tmp/out.txt"; fails=$((fails + 1))
  fi
}

run_case "workflow file has the artifacts, the order and the redaction check" 0 "$wf"

# Broken copy 1: the UI dump upload runs on every result, not only on failure.
sed 's/^        if: failure()$/        if: success()/' "$wf" > "$tmp/no-failure.yml"
run_case "broken copy: UI dump upload not on failure must fail" 1 "$tmp/no-failure.yml"

# Broken copy 2: the redaction check does not delete the log when it fails (not fail closed).
sed 's/^            rm -f -- "\$log"$/            true/' "$wf" > "$tmp/no-delete.yml"
run_case "broken copy: redaction check without the delete must fail" 1 "$tmp/no-delete.yml"

# Broken copy 3: the serial upload is no longer always().
awk 'BEGIN{p=0} /s3\+\. Upload serial log/{p=1} p && /if: always\(\)/{sub(/always\(\)/,"success()"); p=0} {print}' "$wf" > "$tmp/no-always.yml"
run_case "broken copy: serial upload not always() must fail" 1 "$tmp/no-always.yml"

echo ""
if [ "$fails" -ne 0 ]; then echo "bench artifacts offline test: $fails check(s) failed"; exit 1; fi
echo "bench artifacts offline test: all checks passed"

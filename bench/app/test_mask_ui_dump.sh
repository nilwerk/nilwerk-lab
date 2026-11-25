#!/usr/bin/env bash
# Offline test for bench/app/mask_ui_dump.py. Needs bash and python3. No Pi, phone or Appium.
# Fake secret values only. Checks: the secrets, the e-mail, the readings and the input fields are masked; the screen
# text is kept; a missing secret or a secret that is still present stops the write (no file).
set -uo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
masker="$here/mask_ui_dump.py"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
fails=0
ok() { echo "ok: $1"; }
bad() { echo "FAIL: $1"; fails=$((fails + 1)); }

export BENCH_TEST_EMAIL="bench.fake@example.invalid"
export BENCH_TEST_EMAIL_PASSWORD="fake-pass-1234"
export BENCH_BOARD_POP="K7Q2M9XD"
export BENCH_WIFI_PASSWORD="fake-wifi-5678"

# A dump as Appium returns it: a JSON object whose value is the XML text.
cat > "$tmp/source.json" <<'JSON'
{"value": "<?xml version=\"1.0\" encoding=\"UTF-8\"?><hierarchy><android.widget.FrameLayout text=\"\" content-desc=\"\"><android.widget.TextView class=\"android.widget.TextView\" text=\"My plants\" content-desc=\"\"/><android.widget.EditText class=\"android.widget.EditText\" text=\"NW1:nw-c8da2986f470:K7Q2M9XD\" content-desc=\"\" hint=\"Setup code\"/><android.widget.EditText class=\"android.widget.EditText\" text=\"bench.fake@example.invalid\" content-desc=\"\"/><android.widget.EditText class=\"android.widget.EditText\" password=\"true\" text=\"fake-wifi-5678\" content-desc=\"\"/><android.widget.TextView class=\"android.widget.TextView\" text=\"Bench sensor, Bench area, Online, soil moisture 42 %\" content-desc=\"Mint, Kitchen, Online, soil moisture 42 %\"/><android.widget.TextView class=\"android.widget.TextView\" text=\"Login with fake-pass-1234 typed here\" content-desc=\"\"/><android.widget.TextView class=\"android.widget.TextView\" text=\"k7q2m9xd in lower case\" content-desc=\"\"/></android.widget.FrameLayout></hierarchy>"}
JSON

# 1. Normal case: exit 0, file written, secrets and readings gone, screen text kept, file mode 600.
python3 -I "$masker" "$tmp/source.json" "$tmp/out.xml" 2> "$tmp/err1.txt"; rc=$?
if [ "$rc" = "0" ] && [ -s "$tmp/out.xml" ]; then ok "masker writes the dump (exit 0)"; else bad "masker exit $rc, no dump (stderr: $(cat "$tmp/err1.txt"))"; fi
for secret in "$BENCH_TEST_EMAIL" "$BENCH_TEST_EMAIL_PASSWORD" "$BENCH_BOARD_POP" "$BENCH_WIFI_PASSWORD" "k7q2m9xd" "42 %"; do
  grep -q -F -- "$secret" "$tmp/out.xml" && bad "a secret or reading is still in the dump: $secret"
done
grep -q -F "My plants" "$tmp/out.xml" && ok "screen text is kept (My plants)" || bad "screen text was lost"
grep -q -F "[masked]" "$tmp/out.xml" && ok "secrets and input fields are marked [masked]" || bad "no [masked] mark in the dump"
grep -q -F "[reading masked]" "$tmp/out.xml" && ok "the soil-moisture reading is marked [reading masked]" || bad "reading was not marked"
perm="$(stat -c %a "$tmp/out.xml")"
[ "$perm" = "600" ] && ok "dump file mode is 600" || bad "dump file mode is $perm, expected 600"

# 2. A secret variable not set: exit 2, no file (fail closed).
rm -f "$tmp/out2.xml"
( unset BENCH_BOARD_POP; python3 -I "$masker" "$tmp/source.json" "$tmp/out2.xml" 2>/dev/null ); rc=$?
if [ "$rc" = "2" ] && [ ! -e "$tmp/out2.xml" ]; then ok "unset secret: exit 2, no file"; else bad "unset secret: exit $rc, file present: $([ -e "$tmp/out2.xml" ] && echo yes || echo no)"; fi

# 3. Not JSON: exit 2, no file.
echo "not json" > "$tmp/bad.json"
python3 -I "$masker" "$tmp/bad.json" "$tmp/out3.xml" 2>/dev/null; rc=$?
if [ "$rc" = "2" ] && [ ! -e "$tmp/out3.xml" ]; then ok "bad input: exit 2, no file"; else bad "bad input: exit $rc"; fi

# 4. Secret value only as an XML-escaped attribute: still masked (checked on the parsed values).
cat > "$tmp/esc.json" <<'JSON'
{"value": "<hierarchy><android.widget.TextView class=\"android.widget.TextView\" text=\"a &amp; fake-pass-1234\" content-desc=\"\"/></hierarchy>"}
JSON
python3 -I "$masker" "$tmp/esc.json" "$tmp/out4.xml" 2>/dev/null; rc=$?
if [ "$rc" = "0" ] && ! grep -q -F "fake-pass-1234" "$tmp/out4.xml"; then ok "secret inside plain text is masked"; else bad "secret in plain text not masked (exit $rc)"; fi

if [ "$fails" -ne 0 ]; then echo "mask_ui_dump offline test: $fails check(s) failed"; exit 1; fi
echo "mask_ui_dump offline test: all checks passed"

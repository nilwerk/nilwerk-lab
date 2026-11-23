#!/usr/bin/env bash
# bench/app/run_appium.sh: bench step d ("d. App flow on phone"). Device flow in the real (Supabase) app build, through an
# Appium 2 server (UiAutomator2) with W3C element calls. Labels are read from projects/plant-monitor/app/strings/en.json at
# run time. No coordinates. Screen order (file, string key):
#   0. launch         Welcome title app.name (src/screens/WelcomeScreen.tsx). The MOCK build is refused (app.mockBanner, App.tsx).
#   1. sign in        welcome.haveAccount (WelcomeScreen.tsx) -> auth.email, auth.password, auth.signIn.submit
#                     (src/screens/AuthFormScreen.tsx) -> plants.title "My plants" (App.tsx shows PlantsScreen when signed in).
#   2. add sensor     nav.profile tab (src/ui/TabBar.tsx) -> setup.addSensor (ProfileScreen.tsx) -> setup.findSensor
#                     (src/screens/setup/SetupSteps.tsx ReadyStep) -> the device "Sensor NW-<last 6 of hw_id>," (setup.ready.device)
#                     -> setup.connect.codeLabel = NW1:<hw_id>:<pop>, setup.connect.submit (ConnectStep)
#                     -> setup.wifi.title, setup.wifi.other, setup.wifi.ssidLabel, setup.wifi.passwordLabel, setup.wifi.continue (WifiStep)
#                     -> setup.name.label, setup.name.submit (NameStep) -> setup.link.title (LinkingStep)
#                     -> setup.photo.title, setup.photo.skip (PhotoStep) -> setup.details.name / area / city, setup.details.save
#                     (DetailsStep) -> setup.done.title, or setup.move.title + setup.move.move (MoveChoiceStep)
#                     -> setup.done.seePlant (DoneStep). Files: src/screens/setup/SetupFlow.tsx, setupState.ts.
#   3. first reading  nav.plants tab -> plants.title -> the row of this run's plant (plants.row.a11y, src/screens/PlantsScreen.tsx)
#                     shows a reading. Looks again after plants.refresh. The value is not read or printed.
#
# Fails closed: every input is checked before the phone or the Appium server is contacted. Each failure prints
# "d. app flow: <step>: <reason>" and stops the step.
#
# Secrets, from the environment only, never printed: BENCH_TEST_EMAIL, BENCH_TEST_EMAIL_PASSWORD, BENCH_BOARD_POP (the 8-character
# setup code, the PoP part of the label), BENCH_WIFI_SSID, BENCH_WIFI_PASSWORD, BENCH_ANDROID_SERIAL. Values reach Appium only
# through a JSON file in a temporary folder that is deleted on exit.
#
# Other inputs: BENCH_BOARD_HW_ID (repository variable, nw-<12 hex>; the label needs it, and the scanned name is NW- plus its last
# 6 characters). BENCH_FIRST_READING_WAIT_S (seconds): OWNER/KAI INPUT, the upload interval decides it, so there is no default.
# BENCH_SENSOR_NAME, BENCH_PLANT_NAME_PREFIX, BENCH_PLANT_AREA, BENCH_PLANT_CITY: non-secret test names (defaults below). The
# plant name gets a per-run suffix, so an older plant with the same name cannot pass the reading check.
#
# Not checked here: that the phone starts signed out (Appium's default noReset=false clears app data; not verified on the
# phone), that Bluetooth is on (the app shows its own message), and that the BLE setup window is open (see the PR).
set -euo pipefail

step_name=""
fail() { echo "::error::d. app flow: ${step_name:+${step_name}: }$1"; exit 1; }
ok() { echo "d. app flow: ${step_name}: ok"; }

root="$(cd "$(dirname "$0")/../.." && pwd)"
app="$root/projects/plant-monitor/app"
strings="$app/strings/en.json"

# ---- 0. Strings and inputs. Nothing here contacts the phone or the Appium server. ----
keys=(app.name app.mockBanner welcome.haveAccount auth.email auth.password auth.signIn.submit plants.title
  auth.error.invalidCredentials auth.error.network auth.error.notConfigured auth.error.unknown
  nav.profile nav.plants setup.addSensor setup.findSensor setup.ready.title setup.ready.device
  setup.connect.title setup.connect.codeLabel setup.connect.submit setup.wifi.title setup.wifi.other
  setup.wifi.ssidLabel setup.wifi.passwordLabel setup.wifi.continue setup.name.title setup.name.label setup.name.submit
  setup.photo.title setup.photo.skip setup.details.title setup.details.name setup.details.area setup.details.city
  setup.details.save setup.details.saveError setup.done.title setup.done.seePlant setup.move.title setup.move.move
  setup.linked.title setup.notMoved.title setup.linked.unknownTitle
  setup.linkError.wifi.title setup.linkError.owned.title setup.linkError.claim.title
  plants.refresh plants.row.a11y)
declare -A T
dump="$(python3 -I - "$strings" "${keys[@]}" <<'PY'
import json, sys
strings = json.load(open(sys.argv[1], encoding="utf-8"))
out = []
for key in sys.argv[2:]:
    value = strings.get(key)
    if not isinstance(value, str):
        sys.exit(1)
    out.append(key + "\t" + value)
print("\n".join(out))
PY
)" || fail "a string key is missing from projects/plant-monitor/app/strings/en.json"
while IFS=$'\t' read -r k v; do T["$k"]="$v"; done <<< "$dump"

[ -n "${T[app.name]:-}" ] || fail "screen expectation missing: owner or app owner input needed (app.name not readable from projects/plant-monitor/app/strings/en.json)"
pkg="$(sed -n "s/^ *package: '\([A-Za-z0-9_.]*\)',\{0,1\}$/\1/p" "$app/app.config.ts" | head -n 1)"
[ -n "$pkg" ] || fail "app package id not found in projects/plant-monitor/app/app.config.ts"

[ -n "${BENCH_ANDROID_SERIAL:-}" ] || fail "secret BENCH_ANDROID_SERIAL is not set (value not printed)"
[ -n "${BENCH_TEST_EMAIL:-}" ] || fail "secret BENCH_TEST_EMAIL is not set (value not printed)"
[ -n "${BENCH_TEST_EMAIL_PASSWORD:-}" ] || fail "secret BENCH_TEST_EMAIL_PASSWORD is not set (value not printed)"
[ -n "${BENCH_WIFI_SSID:-}" ] || fail "secret BENCH_WIFI_SSID is not set (value not printed)"
[ -n "${BENCH_WIFI_PASSWORD:-}" ] || fail "secret BENCH_WIFI_PASSWORD is not set (value not printed)"
hw="${BENCH_BOARD_HW_ID:-}"
[[ "$hw" =~ ^nw-[0-9a-f]{12}$ ]] || fail "BENCH_BOARD_HW_ID is not set or is not nw-<12 hex> (value not printed)"
pop="$(printf '%s' "${BENCH_BOARD_POP:-}" | tr '[:lower:]' '[:upper:]')"
[[ "$pop" =~ ^[0-9A-HJKMNP-TV-Z]{8}$ ]] || fail "secret BENCH_BOARD_POP is not set or is not an 8-character setup code (value not printed)"
[[ "${BENCH_FIRST_READING_WAIT_S:-}" =~ ^[1-9][0-9]{0,4}$ ]] || fail "BENCH_FIRST_READING_WAIT_S is not set: owner or Kai input needed (the upload interval decides how long to wait for the first reading)"

export BENCH_SENSOR_CODE="NW1:${hw}:${pop}"
export BENCH_WIFI_SSID BENCH_WIFI_PASSWORD
export BENCH_SENSOR_NAME="${BENCH_SENSOR_NAME:-Bench sensor}"
export BENCH_PLANT_AREA="${BENCH_PLANT_AREA:-Bench room}"
export BENCH_PLANT_CITY="${BENCH_PLANT_CITY:-Bench city}"
run_stamp="$(date -u +%m%d%H%M%S)"
export BENCH_PLANT_NAME="${BENCH_PLANT_NAME_PREFIX:-Bench plant} ${run_stamp}"
name_re='^[A-Za-z0-9 _-]{1,40}$'
for n in BENCH_SENSOR_NAME BENCH_PLANT_AREA BENCH_PLANT_CITY BENCH_PLANT_NAME; do
  [[ "${!n}" =~ $name_re ]] || fail "$n has characters or a length this script does not allow (use letters, digits, space, _ or -)"
done
dev_name="NW-${hw: -6}"   # advertised name: NW- plus the last 6 hex of hw_id (app: src/provisioning/label.ts advertisedName)

appium_url="${APPIUM_URL:-http://localhost:4723}"
work="$(mktemp -d "${RUNNER_TEMP:-/tmp}/bench-appium.XXXXXX")"
chmod 700 "$work"
sid=""
cleanup() {
  if [ -n "$sid" ]; then curl -sS -o /dev/null -X DELETE "$appium_url/session/$sid" || true; fi
  rm -rf "$work"
}
trap cleanup EXIT

# ---- helpers: UiAutomator selectors and W3C element calls ----

# selector <out> <kind> <value>. kind: text | textStarts | desc | descStarts | descMatches; ":click" added = clickable only.
selector() {
  python3 -I - "$1" "$2" "$3" <<'PY'
import json, sys
out, kind, value = sys.argv[1], sys.argv[2], sys.argv[3]
click = kind.endswith(":click")
if click:
    kind = kind[:-len(":click")]
q = value.replace("\\", "\\\\").replace('"', '\\"')
expr = {
    "text": f'new UiSelector().text("{q}")',
    "textStarts": f'new UiSelector().textStartsWith("{q}")',
    "desc": f'new UiSelector().description("{q}")',
    "descStarts": f'new UiSelector().descriptionStartsWith("{q}")',
    "descMatches": f'new UiSelector().descriptionMatches("{q}")',
}[kind]
if click:
    expr += ".clickable(true)"
with open(out, "w", encoding="utf-8") as f:
    json.dump({"using": "-android uiautomator", "value": expr}, f)
PY
}

# probe <kind> <value>: one look for an element. Sets el when found.
probe() {
  selector "$work/sel.json" "$1" "$2"
  local code
  code="$(curl -sS -o "$work/el.json" -w '%{http_code}' -H 'Content-Type: application/json' \
    --data-binary @"$work/sel.json" "$appium_url/session/$sid/element")" || code="000"
  el=""
  if [ "$code" = "200" ]; then
    el="$(python3 -I -c 'import json, sys
v = json.load(open(sys.argv[1], encoding="utf-8"))["value"]
print(v.get("element-6066-11e5-a328-0025ce0bfe10") or v.get("ELEMENT") or "")' "$work/el.json")" || el=""
  fi
  [ -n "$el" ]
}

# wait_el <tries> <kind> <value>: up to <tries> looks, 2 s apart.
wait_el() {
  local _
  for _ in $(seq 1 "$1"); do
    if probe "$2" "$3"; then return 0; fi
    sleep 2
  done
  return 1
}

# wait_any <tries> <text>...: exact text. Sets hit to the first text that shows up; returns 1 if none does.
wait_any() {
  local tries="$1" t _
  shift
  for _ in $(seq 1 "$tries"); do
    for t in "$@"; do
      if probe text "$t"; then hit="$t"; return 0; fi
    done
    sleep 2
  done
  return 1
}

post_el() { # post_el <click|clear>
  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' --data-binary '{}' \
    "$appium_url/session/$sid/element/$el/$1")" || code="000"
  [ "$code" = "200" ] || fail "the phone did not accept the $1 command (HTTP $code)"
}

# tap <label>: the button, choice or tab whose accessibility label is <label>
tap() {
  wait_el 30 "desc:click" "$1" || fail "\"$1\" not shown on the screen"
  post_el click
}

# field <label> <env name>: focuses the field labelled <label> and types the value of <env name>. The value is never printed.
field() {
  wait_el 30 desc "$1" || fail "field \"$1\" not shown on the screen"
  post_el click
  python3 -I - "$2" "$work/value.json" <<'PY' || fail "the input for $2 is not set (value not printed)"
import json, os, sys
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump({"text": os.environ[sys.argv[1]]}, f)
PY
  post_el clear
  local code
  code="$(curl -sS -o /dev/null -w '%{http_code}' -X POST -H 'Content-Type: application/json' \
    --data-binary @"$work/value.json" "$appium_url/session/$sid/element/$el/value")" || code="000"
  rm -f "$work/value.json"
  [ "$code" = "200" ] || fail "typing into \"$1\" was not accepted (HTTP $code)"
}

# ---- session and launch (the launch check and the app.name check are kept) ----
step_name="0. launch"
python3 -I - "$pkg" "$work/session.json" <<'PY'
import json, os, sys
caps = {
    "platformName": os.environ.get("APPIUM_PLATFORM_NAME", "Android"),
    "appium:automationName": os.environ.get("APPIUM_AUTOMATION_NAME", "UiAutomator2"),
    "appium:udid": os.environ["BENCH_ANDROID_SERIAL"],
    "appium:appPackage": sys.argv[1],
    # The launch activity must be named: without it Appium sends "am start -a MAIN -c LAUNCHER" with no package and the
    # device answers "Intent does not match any activities" (run 45219867846, step d).
    "appium:appActivity": os.environ.get("APPIUM_APP_ACTIVITY", ".MainActivity"),
    # The app's Bluetooth and location permissions are granted by Appium, so no system dialog has to be tapped.
    "appium:autoGrantPermissions": True,
    "appium:newCommandTimeout": 120,
}
with open(sys.argv[2], "w", encoding="utf-8") as f:
    json.dump({"capabilities": {"alwaysMatch": caps}}, f)
PY
code="$(curl -sS -o "$work/new.json" -w '%{http_code}' -H 'Content-Type: application/json' \
  --data-binary @"$work/session.json" "$appium_url/session")" || code="000"
[ "$code" = "200" ] || fail "Appium did not start a session at APPIUM_URL (HTTP ${code})"
sid="$(python3 -I -c 'import json, sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["value"]["sessionId"])' "$work/new.json")" \
  || fail "Appium reply has no session id"

wait_el 30 text "${T[app.name]}" || fail "first screen title '${T[app.name]}' not found in ${pkg} after 30 tries"
probe text "${T[app.mockBanner]}" && fail "the MOCK build is installed, not the real app; nothing tested"
echo "d. app flow: launch: first screen title '${T[app.name]}' found in the app package ${pkg}"

# ---- 1. sign in with the test account ----
step_name="1. sign in"
probe text "${T[plants.title]}" && fail "the app starts already signed in; the bench must start signed out"
tap "${T[welcome.haveAccount]}"
field "${T[auth.email]}" BENCH_TEST_EMAIL
field "${T[auth.password]}" BENCH_TEST_EMAIL_PASSWORD
tap "${T[auth.signIn.submit]}"
wait_any 60 "${T[plants.title]}" "${T[auth.error.invalidCredentials]}" "${T[auth.error.network]}" \
  "${T[auth.error.notConfigured]}" "${T[auth.error.unknown]}" || fail "no answer to the sign-in in time"
[ "$hit" = "${T[plants.title]}" ] || fail "the server did not accept the test sign-in (screen: \"$hit\")"
ok

# ---- 2. add a sensor: find, pair with the setup code, Wi-Fi, name, photo, plant details, done ----
step_name="2. add sensor"
tap "${T[nav.profile]}"
tap "${T[setup.addSensor]}"
tap "${T[setup.findSensor]}"
# The scan result is a button. Its accessibility label is "Sensor <name>, signal <bars> of 3".
dev_line="$(python3 -I -c 'import sys; print(sys.argv[1].replace("{name}", sys.argv[2]).replace("{bars}", "0"))' "${T[setup.ready.device]}" "$dev_name")"
dev_prefix="${dev_line%%, signal*},"
wait_el 45 "descStarts:click" "$dev_prefix" || fail "sensor $dev_name not in the scan (the BLE setup window is closed, or the phone is too far away)"
post_el click
wait_el 30 text "${T[setup.connect.title]}" || fail "the connect step did not open after the sensor was chosen"
field "${T[setup.connect.codeLabel]}" BENCH_SENSOR_CODE
tap "${T[setup.connect.submit]}"
wait_any 180 "${T[setup.wifi.title]}" || fail "the Wi-Fi step did not open after the setup code was sent (code refused, or the link dropped)"
tap "${T[setup.wifi.other]}"
field "${T[setup.wifi.ssidLabel]}" BENCH_WIFI_SSID
field "${T[setup.wifi.passwordLabel]}" BENCH_WIFI_PASSWORD
tap "${T[setup.wifi.continue]}"
wait_el 30 text "${T[setup.name.title]}" || fail "the name step did not open after Wi-Fi was entered"
field "${T[setup.name.label]}" BENCH_SENSOR_NAME
tap "${T[setup.name.submit]}"
# Linking: the sensor joins Wi-Fi and is claimed. Stop on an error screen; go on at the photo step.
photo="${T[setup.photo.title]}"
wait_any 180 "$photo" "${T[setup.linkError.wifi.title]}" "${T[setup.linkError.owned.title]}" "${T[setup.linkError.claim.title]}" \
  || fail "linking did not reach the photo step in time"
[ "$hit" = "$photo" ] || fail "the sensor could not be linked (stopped on \"$hit\")"
tap "${T[setup.photo.skip]}"
wait_el 30 text "${T[setup.details.title]}" || fail "the plant details step did not open"
field "${T[setup.details.name]}" BENCH_PLANT_NAME
field "${T[setup.details.area]}" BENCH_PLANT_AREA
field "${T[setup.details.city]}" BENCH_PLANT_CITY
tap "${T[setup.details.save]}"
done_title="${T[setup.done.title]}"; move_title="${T[setup.move.title]}"
wait_any 120 "$done_title" "$move_title" "${T[setup.linked.title]}" "${T[setup.notMoved.title]}" \
  "${T[setup.linked.unknownTitle]}" "${T[setup.details.saveError]}" || fail "the plant save was not answered in time"
if [ "$hit" = "$move_title" ]; then
  # The sensor already had a plant (an earlier run). Move it to the plant of this run, the only write this screen offers.
  tap "${T[setup.move.move]}"
  wait_any 120 "$done_title" || fail "the move to the new plant was not confirmed in time"
elif [ "$hit" != "$done_title" ]; then
  fail "the plant was not saved (stopped on \"$hit\")"
fi
tap "${T[setup.done.seePlant]}"
ok

# ---- 3. first reading in the cloud: this run's plant shows a reading on My plants ----
step_name="3. first reading"
tap "${T[nav.plants]}"
wait_el 30 text "${T[plants.title]}" || fail "My plants did not open"
row_re="$(python3 -I - "${T[plants.row.a11y]}" "$BENCH_PLANT_NAME" "$BENCH_PLANT_AREA" <<'PY'
import re, sys
template, name, area = sys.argv[1], sys.argv[2], sys.argv[3]
# Row label "{name}, {area}, {status}, soil moisture {value}". {value} must be a number, not "No reading". Not printed.
values = {"name": re.escape(name), "area": re.escape(area), "status": ".*", "value": "[0-9]+ %"}
out, pos = "", 0
for m in re.finditer(r"\{(\w+)\}", template):
    out += re.escape(template[pos:m.start()]) + values[m.group(1)]
    pos = m.end()
print(out + re.escape(template[pos:]))
PY
)" || fail "the plant row label could not be built from strings/en.json"
deadline=$(( $(date +%s) + BENCH_FIRST_READING_WAIT_S ))
while ! probe descMatches "$row_re"; do
  [ "$(date +%s)" -lt "$deadline" ] || fail "no reading for this run's plant on My plants within ${BENCH_FIRST_READING_WAIT_S} s"
  tap "${T[plants.refresh]}"
  sleep 30
done
ok
echo "d. app flow: PASS: sign-in, sensor setup in the app, and a first reading for this run's plant on My plants (value not read)"

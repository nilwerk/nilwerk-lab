#!/usr/bin/env python3
"""Host tests for the per-unit security-2 tool and its firmware names (task 4.F2b). No hardware, no ESP-IDF.
Prints 'ok'/'FAIL' lines, exit 1 on any FAIL. The tool path can be overridden for the mutation script: check_sec2.py [tool.py]."""
import hashlib, importlib.util, io, contextlib, os, pathlib, re, stat, sys, tempfile

here = pathlib.Path(__file__).resolve().parent
fw = here.parents[1]
tool_path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else fw / "tools" / "nw_sec2_gen.py"
spec = importlib.util.spec_from_file_location("nw_sec2_gen", tool_path); T = importlib.util.module_from_spec(spec); spec.loader.exec_module(T)
fails = []
def check(ok, msg):
    print(("ok   " if ok else "FAIL ") + msg)
    if not ok: fails.append(msg)

# --- group constant derived independently (RFC 3526 group 15 = RFC 5054 3072-bit: 2^3072-2^3008-1+2^64*(floor(2^2942*pi)+1690314))
def atan_inv(x, one):
    t = one // x; s = t; n = 1; sign = -1
    while t:
        t //= x * x; n += 2; s += sign * (t // n); sign = -sign
    return s
pi = (4 * (4 * atan_inv(5, 1 << 3006) - atan_inv(239, 1 << 3006))) >> 64
N_ref = 2**3072 - 2**3008 - 1 + 2**64 * (pi + 1690314)
check(T.N == N_ref, "SRP modulus equals the RFC 3526/5054 3072-bit prime derived from pi")
check(T.N.bit_length() == 3072 and T.G == 5, "3072-bit group, g = 5 (RFC 5054)")
def mr(n, bases=(2, 3, 5, 7, 11, 13, 17, 19)):
    d, r = n - 1, 0
    while d % 2 == 0: d //= 2; r += 1
    for a in bases:
        x = pow(a, d, n)
        if x in (1, n - 1): continue
        for _ in range(r - 1):
            x = x * x % n
            if x == n - 1: break
        else: return False
    return True
check(mr(T.N) and mr((T.N - 1) // 2), "modulus is a probable safe prime")
check(T.USER == "wifiprov" and T.SALT_LEN == 16 and T.VER_LEN == 384 and T.POP_LEN == 8, "constants: user wifiprov, salt 16, verifier 384, PoP 8 (contract PR #129)")

# --- derivation
salt = bytes(range(16)); pop = "7KQ2M9XD"
v = T.derive(salt, pop)
check(len(v) == 384, "verifier is fixed width 384 bytes")
check(hashlib.sha256(v).hexdigest() == "74ce4c82cc8001d6385c5a316d1fe57ecac59fd52271c40247927939808c1b6a",
      "pinned vector (regression pin from this tool; NOT an external known answer)")
x = int.from_bytes(hashlib.sha512(salt + hashlib.sha512(b"wifiprov:" + pop.encode()).digest()).digest(), "big")
check(int.from_bytes(v, "big") == pow(5, x, N_ref), "v = g^x mod N with x = SHA512(salt | SHA512(user:PoP))")
check(T.derive(salt, pop) == v, "deterministic")
check(T.derive(bytes([1]) + salt[1:], pop) != v, "different salt -> different verifier")
check(T.derive(salt, "7KQ2M9XE") != v, "different PoP -> different verifier")
check(T.derive(salt, pop, user="other") != v, "user name is part of the hash")
check(pop.encode() not in v and pop.encode() not in salt, "PoP not contained in stored data")
try:
    import srp   # optional cross-check against pysrp, the library ESP-IDF tooling uses
    # PyPI srp has no NG_3072: pass the RFC 5054 3072-bit group as NG_CUSTOM (review C2, PR #132)
    s2, v2 = srp.create_salted_verification_key(T.USER, pop, srp.SHA512, srp.NG_CUSTOM,
                                                format(T.N, "x").encode(), b"5", salt_len=16)
    check(T.derive(s2, pop) == v2.rjust(384, b"\0"), "matches pysrp create_salted_verification_key (NG_CUSTOM 3072, g=5, SHA-512)")
except Exception as e:   # ImportError, or API differences between srp versions: optional check, never red
    print("SKIP pysrp cross-check not run (%s: %s); UNVERIFIED against pysrp / ESP-IDF" % (type(e).__name__, e))
# --- doc pointers must exist (review C1, PR #132): every repo path cited by the tool, overlay and procedure
pm = fw.parent   # projects/plant-monitor
cited = set()
for src in (tool_path, fw / "sdkconfig.defaults.setup"):
    cited |= set(re.findall(r"\b((?:tests|docs|firmware)/[\w./-]+\.(?:md|py|c|h|setup))\b", src.read_text()))
check(cited >= {"tests/procedures/4.F2b-sec2-provisioning.md"}, "tool/overlay cite the bench procedure path")
check("docs/BENCH-SEC2.md" not in "".join(p.read_text() for p in (tool_path, fw / "sdkconfig.defaults.setup")), "no stale docs/BENCH-SEC2.md pointer")
for c in sorted(cited):
    check((pm / c).exists() or (fw / c.removeprefix("firmware/")).exists(), "cited path exists: " + c)
for bad in ("", "7KQ2M9X", "7KQ2M9XDD", "7KQ2M9XI", "7kq2m9xd", "7KQ2M9XL", "7KQ2M9X!"):
    try: T.derive(salt, bad); check(False, "PoP %r rejected" % bad)
    except ValueError: check(True, "PoP %r rejected" % bad)
try: T.derive(salt[:15], pop); check(False, "short salt rejected")
except ValueError: check(True, "short salt rejected")
pops = {T.new_pop() for _ in range(50)}
check(len(pops) == 50 and all(T.valid_pop(p) for p in pops), "new_pop: valid, not repeating")
check(set("".join(T.new_pop() for _ in range(600))) == set("0123456789ABCDEFGHJKMNPQRSTVWXYZ"), "PoP generator reaches all 32 symbols (miss chance < 1e-30)")
check(all(set(T.new_pop()) <= set("0123456789ABCDEFGHJKMNPQRSTVWXYZ") for _ in range(20)), "PoP alphabet is Crockford (no I L O U)")

# --- CSV + label
csv = T.csv_text(salt, v)
check(T.parse_csv(csv) == (salt, v), "CSV round trip")
check("nw_sec2,namespace" in csv and "\nsalt,data,hex2bin," in csv and "\nverifier,data,hex2bin," in csv, "CSV uses namespace nw_sec2, keys salt and verifier")
for broken in (csv.replace("nw_sec2", "nw_sec3"), csv.replace("\nsalt,", "\nsalt2,"), csv.replace("hex2bin", "string")):
    try: T.parse_csv(broken); check(False, "broken CSV rejected")
    except (ValueError, IndexError): check(True, "broken CSV rejected")
check(T.label_text("nw-a1b2c3d4e5f6", pop) == "NW1:nw-a1b2c3d4e5f6:7KQ2M9XD", "label text NW1:<hw_id>:<pop>")

# --- gen / check end to end
def run(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try: T.main(list(args)); code = 0
        except SystemExit as e: code = e.code if isinstance(e.code, int) else 1
    return code, out.getvalue() + err.getvalue()
with tempfile.TemporaryDirectory() as td:
    code, log = run("gen", "--hw-id", "nw-a1b2c3d4e5f6", "--out", td, "--pop", pop)
    f_csv, f_lab = pathlib.Path(td) / "nw-a1b2c3d4e5f6.nvs.csv", pathlib.Path(td) / "nw-a1b2c3d4e5f6.label.txt"
    check(code == 0 and f_csv.exists() and f_lab.exists(), "gen writes csv + label")
    s_, v_ = T.parse_csv(f_csv.read_text())
    check(pop not in log and s_.hex() not in log and v_.hex() not in log and v_.hex()[:16] not in log, "stdout shows no PoP, salt or verifier")
    check("verifier_fp=" + T.fingerprint(v_) in log, "stdout shows only the fingerprint")
    check(stat.S_IMODE(os.stat(f_csv).st_mode) == 0o600 and stat.S_IMODE(os.stat(f_lab).st_mode) == 0o600, "files are 0600")
    check(f_lab.read_text().strip() == "NW1:nw-a1b2c3d4e5f6:" + pop, "label file content")
    check(run("check", "--csv", str(f_csv), "--label", str(f_lab))[0] == 0, "check: MATCH")
    code, log = run("gen", "--hw-id", "nw-a1b2c3d4e5f6", "--out", td, "--pop", pop)
    check(code != 0, "gen refuses to overwrite an existing unit's files")
    f_lab2 = pathlib.Path(td) / "other.label.txt"; f_lab2.write_text("NW1:nw-a1b2c3d4e5f6:7KQ2M9XE\n")
    check(run("check", "--csv", str(f_csv), "--label", str(f_lab2))[0] == 1, "check: MISMATCH on another PoP")
    code, _ = run("gen", "--hw-id", "nw-a1b2c3d4e5f6", "--out", td + "/b")
    s1, _v1 = T.parse_csv((pathlib.Path(td) / "b/nw-a1b2c3d4e5f6.nvs.csv").read_text())
    code, _ = run("gen", "--hw-id", "nw-a1b2c3d4e5f6", "--out", td + "/c")
    s2_, _v2 = T.parse_csv((pathlib.Path(td) / "c/nw-a1b2c3d4e5f6.nvs.csv").read_text())
    check(s1 != s2_ and len(s1) == 16, "two runs give different random salts")
    for bad in ("nw-A1B2C3D4E5F6", "nw-a1b2", "a1b2c3d4e5f6", "nw-a1b2c3d4e5fg"):
        check(run("gen", "--hw-id", bad, "--out", td + "/d")[0] != 0, "hw_id %r rejected" % bad)
    check(run("gen", "--hw-id", "nw-a1b2c3d4e5f6", "--out", td + "/e", "--pop", "short")[0] != 0, "bad --pop rejected")
repo = fw.parents[2]
code, log = run("gen", "--hw-id", "nw-a1b2c3d4e5f6", "--out", str(repo / "projects" / "_must_not_exist_sec2"))
ok_refused = code != 0 and not (repo / "projects" / "_must_not_exist_sec2").exists()
import shutil; shutil.rmtree(repo / "projects" / "_must_not_exist_sec2", ignore_errors=True)   # a mutant that lets gen run must not leave files in the repo
check(ok_refused, "gen refuses --out inside the git work tree")

# --- names match the firmware (contract PR #129) and the repo keeps no per-unit secrets
idf = (fw / "components/provisioning/src/nw_prov_idf.c").read_text()
h = (fw / "components/provisioning/include/nw_sec2.h").read_text()
c = (fw / "components/provisioning/src/nw_sec2.c").read_text()
check(f'nvs_open("{T.NS}"' in idf and f'nvs_get_blob(h, "{T.KEY_SALT}"' in idf and f'nvs_get_blob(h, "{T.KEY_VER}"' in idf, "tool NVS names == nw_prov_idf.c")
check(f'NW_SEC2_NVS_NAMESPACE "{T.NS}"' in h and f'NW_SEC2_KEY_SALT "{T.KEY_SALT}"' in h and f'NW_SEC2_KEY_VERIFIER "{T.KEY_VER}"' in h, "tool NVS names == nw_sec2.h")
check(f"NW_SEC2_SALT_LEN {T.SALT_LEN}u" in h and f"NW_SEC2_VERIFIER_LEN {T.VER_LEN}u" in h, "tool sizes == nw_sec2.h")
check("nw_sec2_valid(salt, *sl, ver, *vl)" in idf, "nw_prov_idf.c validates salt/verifier before advertising")
check("nw_sec2.c" in (fw / "components/provisioning/CMakeLists.txt").read_text(), "nw_sec2.c is in the component build")
setup = (fw / "sdkconfig.defaults.setup").read_text()
check(re.search(r"^CONFIG_PLANT_SETUP_FLOW=y$", setup, re.M) is not None and "CONFIG_PLANT_API" not in setup, "setup overlay: SETUP_FLOW=y, no URL or secret")
check(re.search(r"^CONFIG_PLANT_SETUP_FLOW=n$", (fw / "sdkconfig.defaults.v1").read_text(), re.M) is not None, "v1 defaults still SETUP_FLOW=n (bench build unchanged)")
gi = (repo / ".gitignore").read_text()
check("provision-out/" in gi, ".gitignore covers provision-out/")
tracked = [p for p in (fw.parents[0] / "tests").rglob("*") if p.suffix in (".csv",) and "nvs" in p.name]
check(not tracked, "no *.nvs.csv in tracked test dirs")
print(f"{len(fails)} failed")
sys.exit(1 if fails else 0)

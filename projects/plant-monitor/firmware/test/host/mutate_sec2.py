#!/usr/bin/env python3
"""Mutation check for the security-2 tool and validator (task 4.F2b): each mutant must make its test fail.
Usage: mutate_sec2.py [cc]. Works on temp copies, never edits the sources. Exit 1 when a mutant survives or does not compile/apply."""
import pathlib, shutil, subprocess, sys, tempfile

here = pathlib.Path(__file__).resolve().parent
fw = here.parents[1]
cc = sys.argv[1] if len(sys.argv) > 1 else "cc"
TOOL = fw / "tools" / "nw_sec2_gen.py"
PROV = fw / "components" / "provisioning"
PY = [  # (old, new, what)
 ('USER = "wifiprov"', 'USER = "wifiprov2"', "SRP user name"),
 ("SALT_LEN, VER_LEN = 16, 384", "SALT_LEN, VER_LEN = 32, 384", "salt length"),
 ("SALT_LEN, VER_LEN = 16, 384", "SALT_LEN, VER_LEN = 16, 383", "verifier width"),
 ("G = 5", "G = 2", "generator"),
 ("hashlib.sha512(salt + inner)", "hashlib.sha512(inner + salt)", "x = H(salt|inner) order"),
 ("hashlib.sha512((user + \":\" + pop)", "hashlib.sha512((pop + \":\" + user)", "inner hash order"),
 ("hashlib.sha512(salt + inner)", "hashlib.sha256(salt + inner)", "hash algorithm"),
 ('NS, KEY_SALT, KEY_VER = "nw_sec2"', 'NS, KEY_SALT, KEY_VER = "nw_sec3"', "NVS namespace"),
 ('"salt", "verifier"', '"salt", "verify"', "NVS verifier key"),
 ("0o600)", "0o644)", "file mode"),
 ("if inside_git_tree(a.out): sys.exit", "if False: sys.exit", "git tree refusal"),
 ("if f_csv.exists() or f_lab.exists(): sys.exit", "if False: sys.exit", "existing files refusal"),
 ("verifier_fp=%s files", "verifier=%s files", "fingerprint label"),
 ("a.hw_id, fingerprint(ver), a.hw_id, a.hw_id))", "a.hw_id, ver.hex(), a.hw_id, a.hw_id))", "verifier printed"),
 ("a.hw_id, fingerprint(ver)", "a.hw_id, pop", "PoP printed"),
 ("secrets.token_bytes(SALT_LEN)", "bytes(SALT_LEN)", "constant salt"),
 ("CROCKFORD[b % 32]", "CROCKFORD[b % 31]", "PoP alphabet reach"),
 ("all(c in CROCKFORD for c in p)", "True", "PoP alphabet check"),
 ("len(p) == POP_LEN and", "", "PoP length check"),
 ("good = len(salt) == SALT_LEN and len(ver) == VER_LEN and derive(salt, m.group(2)) == ver", "good = True", "check always matches"),
 ('"NW1:%s:%s"', '"NW:%s:%s"', "label prefix"),
]
C = [
 ("NW_SEC2_SALT_LEN 16u", "NW_SEC2_SALT_LEN 32u", "salt len constant", "nw_sec2.h"),
 ("NW_SEC2_VERIFIER_LEN 384u", "NW_SEC2_VERIFIER_LEN 256u", "verifier len constant", "nw_sec2.h"),
 ("if (salt_len != NW_SEC2_SALT_LEN || verifier_len != NW_SEC2_VERIFIER_LEN) return false;", "if (salt_len < NW_SEC2_SALT_LEN || verifier_len < NW_SEC2_VERIFIER_LEN) return false;", "exact length", "nw_sec2.c"),
 ("if (salt_len != NW_SEC2_SALT_LEN || verifier_len != NW_SEC2_VERIFIER_LEN) return false;", "if (verifier_len != NW_SEC2_VERIFIER_LEN) return false;", "salt length check", "nw_sec2.c"),
 ("if (uniform(salt, salt_len) || uniform(verifier, verifier_len)) return false;", "if (uniform(verifier, verifier_len)) return false;", "blank salt", "nw_sec2.c"),
 ("if (uniform(salt, salt_len) || uniform(verifier, verifier_len)) return false;", "if (uniform(salt, salt_len)) return false;", "blank verifier", "nw_sec2.c"),
 ("for (size_t i = 1; i < n; i++)", "for (size_t i = 1; i + 1 < n; i++)", "last byte not examined", "nw_sec2.c"),
 ("for (size_t i = 1; i < n; i++)", "for (size_t i = 2; i < n; i++)", "second byte not examined", "nw_sec2.c"),
 ("if (!salt || !verifier) return false;", "", "null guard", "nw_sec2.c"),
]
bad = 0
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    def run_py(src):
        return subprocess.run([sys.executable, str(here / "check_sec2.py"), str(src)], capture_output=True, text=True, cwd=str(here)).returncode
    def run_c(d):
        cmd = [cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-I", str(d / "include"), "-I", str(here), str(here / "test_sec2.c"), str(d / "src" / "nw_sec2.c"), "-o", str(d / "t")]
        c = subprocess.run(cmd, capture_output=True, text=True)
        if c.returncode: return "compile"
        return "pass" if subprocess.run([str(d / "t")], capture_output=True).returncode == 0 else "fail"
    if run_py(TOOL) != 0: print("baseline python check does not pass"); sys.exit(1)
    base = td / "base"; shutil.copytree(PROV, base)
    if run_c(base) != "pass": print("baseline C test does not pass"); sys.exit(1)
    for i, (old, new, what) in enumerate(PY):
        t = TOOL.read_text()
        if t.count(old) != 1: print(f"BAD   py mutant '{what}': pattern found {t.count(old)}x"); bad += 1; continue
        m = td / f"m{i}.py"; m.write_text(t.replace(old, new))
        if run_py(m) == 0: print(f"SURVIVED py: {what}"); bad += 1
        else: print(f"killed   py: {what}")
    for i, (old, new, what, f) in enumerate(C):
        d = td / f"c{i}"; shutil.copytree(PROV, d)
        p = next(q for q in (d / "src" / f, d / "include" / f) if q.exists())
        t = p.read_text()
        if t.count(old) != 1: print(f"BAD   C mutant '{what}': pattern found {t.count(old)}x"); bad += 1; continue
        p.write_text(t.replace(old, new)); r = run_c(d)
        if r == "pass": print(f"SURVIVED C: {what}"); bad += 1
        else: print(f"killed   C: {what} ({r})")
print(f"{bad} problem(s)"); sys.exit(1 if bad else 0)

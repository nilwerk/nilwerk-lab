#!/usr/bin/env python3
"""Per-unit protocomm security-2 provisioning data (task 4.F2b, A-081 answer a, contract PR #129).

Makes, for ONE unit: a random 16-byte SRP6a salt, a verifier v = g^x mod N (RFC 5054 3072-bit group, g = 5, SHA-512,
x = SHA512(salt | SHA512(user ":" PoP)), user = "wifiprov"), written to the NVS namespace "nw_sec2" (blob keys "salt" and
"verifier", the names nw_prov_idf.c reads) as an nvs_partition_gen CSV. The PoP printed on the unit label is NOT stored on the device.

Formula follows the ESP-IDF security-2 tooling (pysrp create_salted_verification_key, SHA-512, NG_3072). Wire compatibility with a real
ESP-IDF 5.4 device and the phone app is UNVERIFIED (no ESP-IDF, no hardware here): bench step B4 in tests/procedures/4.F2b-sec2-provisioning.md is the proof.

SECRETS: the PoP, salt and verifier are per-unit secrets. They are written only under --out, which must be OUTSIDE any git work tree;
stdout/stderr only ever show hw_id and a short verifier fingerprint. Stdlib only.

  gen   --hw-id nw-a1b2c3d4e5f6 --out DIR [--pop XXXXXXXX]   -> DIR/<hw_id>.nvs.csv (0600) and DIR/<hw_id>.label.txt (0600)
  (omit --pop: the default random PoP is right; a --pop value lands in shell history and is for tests only)
  check --csv FILE --label FILE                               -> recompute the verifier from the label PoP and compare
"""
import argparse, base64, hashlib, os, pathlib, re, secrets, stat, sys

USER = "wifiprov"                      # SRP user name, fixed and non-secret (docs/interfaces/ble-provisioning.md, PR #129)
NS, KEY_SALT, KEY_VER = "nw_sec2", "salt", "verifier"   # NVS names, must equal nw_prov_idf.c (checked by check_sec2.py)
SALT_LEN, VER_LEN = 16, 384            # 384 = 3072 bit, fixed width (leading zeros kept)
G = 5
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
POP_LEN = 8                            # 8 chars Crockford base32 = 40 bit (contract table, Label / QR)
HW_RE = re.compile(r"^nw-[0-9a-f]{12}$")
N = int("FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD129024E088A67CC74020BBEA63B139B22514A08798E3404DDEF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7EDEE386BFB5A899FA5AE9F24117C4B1FE649286651ECE45B3DC2007CB8A163BF0598DA48361C55D39A69163FA8FD24CF5F83655D23DCA3AD961C62F356208552BB9ED529077096966D670C354E4ABC9804F1746C08CA18217C32905E462E36CE3BE39E772C180E86039B2783A2EC07A28FB5C55DF06F4C52C9DE2BCBF6955817183995497CEA956AE515D2261898FA051015728E5A8AAAC42DAD33170D04507A33A85521ABDF1CBA64ECFB850458DBEF0A8AEA71575D060C7DB3970F85A6E1E4C7ABF5AE8CDB0933D71E8C94E04A25619DCEE3D2261AD2EE6BF12FFA06D98A0864D87602733EC86A64521F2B18177B200CBBE117577A615D6C770988C0BAD946E208E24FA074E5AB3143DB5BFCE0FD108E4B82D120A93AD2CAFFFFFFFFFFFFFFFF", 16)                      # RFC 3526 group 15 = RFC 5054 3072-bit prime; test derives it independently from pi

def new_pop():
    return "".join(CROCKFORD[b % 32] for b in secrets.token_bytes(POP_LEN))   # 256 is a multiple of 32: no modulo bias

def valid_pop(p):
    return isinstance(p, str) and len(p) == POP_LEN and all(c in CROCKFORD for c in p)

def derive(salt, pop, user=USER):
    if len(salt) != SALT_LEN: raise ValueError("salt must be %d bytes" % SALT_LEN)
    if not valid_pop(pop): raise ValueError("PoP must be %d Crockford base32 characters" % POP_LEN)
    inner = hashlib.sha512((user + ":" + pop).encode()).digest()
    x = int.from_bytes(hashlib.sha512(salt + inner).digest(), "big")
    return pow(G, x, N).to_bytes(VER_LEN, "big")

def label_text(hw_id, pop):
    return "NW1:%s:%s" % (hw_id, pop)

def csv_text(salt, ver):
    return "key,type,encoding,value\n%s,namespace,,\n%s,data,hex2bin,%s\n%s,data,hex2bin,%s\n" % (NS, KEY_SALT, salt.hex(), KEY_VER, ver.hex())

def parse_csv(text):
    rows = [l.split(",") for l in text.strip().splitlines()]
    if rows[0] != ["key", "type", "encoding", "value"] or rows[1] != [NS, "namespace", "", ""] or len(rows) != 4:
        raise ValueError("unexpected CSV layout")
    d = {}
    for r in rows[2:]:
        if r[1:3] != ["data", "hex2bin"]: raise ValueError("unexpected row")
        d[r[0]] = bytes.fromhex(r[3])
    if set(d) != {KEY_SALT, KEY_VER}: raise ValueError("keys must be salt and verifier")
    return d[KEY_SALT], d[KEY_VER]

def fingerprint(ver):
    return hashlib.sha256(ver).hexdigest()[:8]     # non-reversible label for logs; the verifier itself is never printed

def inside_git_tree(path):
    p = pathlib.Path(path).resolve()
    return any((q / ".git").exists() for q in [p, *p.parents])

def write_private(path, text):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)    # O_EXCL: never overwrite a unit's existing secrets
    with os.fdopen(fd, "w") as f: f.write(text)

def cmd_gen(a):
    if not HW_RE.match(a.hw_id): sys.exit("hw_id must look like nw-a1b2c3d4e5f6 (nw- + 12 lowercase hex)")
    if inside_git_tree(a.out): sys.exit("refusing: --out is inside a git work tree; per-unit secrets must never be committed")
    pop = a.pop or new_pop()
    if not valid_pop(pop): sys.exit("PoP must be 8 Crockford base32 characters (0-9 A-Z without I L O U)")
    salt = secrets.token_bytes(SALT_LEN)
    ver = derive(salt, pop)
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    f_csv, f_lab = out / (a.hw_id + ".nvs.csv"), out / (a.hw_id + ".label.txt")
    if f_csv.exists() or f_lab.exists(): sys.exit("refusing: files for %s already exist in --out (never overwrite a unit's secrets)" % a.hw_id)
    write_private(f_csv, csv_text(salt, ver))
    write_private(f_lab, label_text(a.hw_id, pop) + "\n")
    print("ok hw_id=%s verifier_fp=%s files=%s.nvs.csv,%s.label.txt (secrets: not shown)" % (a.hw_id, fingerprint(ver), a.hw_id, a.hw_id))

def cmd_check(a):
    salt, ver = parse_csv(pathlib.Path(a.csv).read_text())
    m = re.match(r"^NW1:(nw-[0-9a-f]{12}):([0-9A-Z]{8})$", pathlib.Path(a.label).read_text().strip())
    if not m: sys.exit("label file is not NW1:<hw_id>:<pop>")
    good = len(salt) == SALT_LEN and len(ver) == VER_LEN and derive(salt, m.group(2)) == ver
    print("%s hw_id=%s verifier_fp=%s" % ("MATCH" if good else "MISMATCH", m.group(1), fingerprint(ver)))
    sys.exit(0 if good else 1)

def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0]); sp = ap.add_subparsers(dest="c", required=True)
    g = sp.add_parser("gen"); g.add_argument("--hw-id", required=True); g.add_argument("--out", required=True); g.add_argument("--pop"); g.set_defaults(f=cmd_gen)
    c = sp.add_parser("check"); c.add_argument("--csv", required=True); c.add_argument("--label", required=True); c.set_defaults(f=cmd_check)
    a = ap.parse_args(argv); a.f(a)

if __name__ == "__main__":
    main()

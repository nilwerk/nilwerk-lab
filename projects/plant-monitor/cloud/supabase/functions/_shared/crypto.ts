// Token helpers (ADR-004, NFR-06). Web-standard APIs only, so the same code runs in Deno (Edge Functions) and Node (tests).
const enc = new TextEncoder();

/** SHA-256 of the token string (UTF-8), as the '\x<hex>' string PostgREST accepts for bytea. */
export async function sha256ByteaHex(token: string): Promise<string> {
  const d = new Uint8Array(await crypto.subtle.digest("SHA-256", enc.encode(token)));
  return "\\x" + Array.from(d, (b) => b.toString(16).padStart(2, "0")).join("");
}

/** New device token: 32 random bytes as 64 hex chars, shown to the device once (openapi /device-claim, ADR-004). */
export function newDeviceToken(): string {
  const b = crypto.getRandomValues(new Uint8Array(32));
  return Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");
}

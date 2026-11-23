// MCP server (task 4.B5): lets the user's own AI client read their own plants. Plain TypeScript, no dependencies:
// runs in Deno (Supabase edge function `mcp`) and Node 22+ (tests). Transport: JSON-RPC 2.0 over HTTP POST (MCP
// Streamable HTTP, single JSON responses, no SSE).
// Requirements: FR-P03 (four read-only tools, per-user API key, revocable), FR-P04 (premium only), FR-P01 (history window),
// FR-P02 (tips come from the guardrailed cache only), FR-A06 (plant status), NFR-06 (key stored hashed, never logged),
// NFR-07 (no data beyond the caller's own rows). Contract: docs/interfaces/mcp-tools.json (ADR-007). Key format and storage: cloud/README.md "MCP API keys".
import { bearer, err, json, sha256Hex, type Deps } from "./lib.ts";

export type McpDeps = Pick<Deps, "rpc">;

/** Key = "nwk_" + 32 random bytes, base64url without padding (43 chars). Only sha256(key) is stored (api_keys.key_hash). FR-P03, NFR-06. */
export const KEY_PATTERN = /^nwk_[A-Za-z0-9_-]{43}$/;
/** Must equal GUARDRAIL_VERSION in tips/guardrails.ts (a test checks it). Tips stored under another version are not returned (FR-P02). */
export const GUARDRAIL_VERSION_EXPECTED = "g1.1";
export const PROTOCOL_VERSION = "2025-06-18";
export const SERVER_INFO = { name: "nilwerk-plant-monitor", version: "0.1.0" };
export const MAX_BODY_BYTES = 16 * 1024;
const TIP_CATEGORIES = ["watering", "light", "temperature", "feeding", "safety", "other"] as const;
const TIP_TEXT_MAX = 400;

// ---------------------------------------------------------------- schema subset (what the contract uses) and a small validator
export interface Schema {
  type?: string | string[]; enum?: unknown[]; format?: string; properties?: Record<string, Schema>; required?: string[];
  additionalProperties?: boolean; items?: Schema; minimum?: number; maximum?: number; minLength?: number; maxLength?: number; default?: unknown;
}
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const DATETIME_RE = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:\d{2})$/;
const isType = (t: string, v: unknown): boolean => {
  switch (t) {
    case "string": return typeof v === "string";
    case "number": return typeof v === "number" && Number.isFinite(v);
    case "integer": return typeof v === "number" && Number.isInteger(v);
    case "boolean": return typeof v === "boolean";
    case "array": return Array.isArray(v);
    case "object": return typeof v === "object" && v !== null && !Array.isArray(v);
    case "null": return v === null;
    default: return false;
  }
};
/** Returns null when `v` matches `s`, otherwise a short message naming the JSON path (never the value). */
export function validate(s: Schema, v: unknown, at = "$"): string | null {
  if (s.type !== undefined) {
    const types = Array.isArray(s.type) ? s.type : [s.type];
    if (!types.some((t) => isType(t, v))) return `${at}: wrong type`;
  }
  if (v === null) return null;
  if (s.enum && !s.enum.includes(v)) return `${at}: not an allowed value`;
  if (typeof v === "string") {
    if (s.minLength !== undefined && v.length < s.minLength) return `${at}: too short`;
    if (s.maxLength !== undefined && v.length > s.maxLength) return `${at}: too long`;
    if (s.format === "uuid" && !UUID_RE.test(v)) return `${at}: not a uuid`;
    if (s.format === "date-time" && (!DATETIME_RE.test(v) || Number.isNaN(Date.parse(v)))) return `${at}: not a date-time`;
  }
  if (typeof v === "number") {
    if (s.minimum !== undefined && v < s.minimum) return `${at}: below minimum`;
    if (s.maximum !== undefined && v > s.maximum) return `${at}: above maximum`;
  }
  if (Array.isArray(v) && s.items) {
    for (let i = 0; i < v.length; i++) { const e = validate(s.items, v[i], `${at}[${i}]`); if (e) return e; }
  }
  if (typeof v === "object" && v !== null && !Array.isArray(v)) {
    const o = v as Record<string, unknown>;
    for (const k of s.required ?? []) if (!(k in o)) return `${at}.${k}: required`;
    for (const [k, sub] of Object.entries(s.properties ?? {})) if (k in o) { const e = validate(sub, o[k], `${at}.${k}`); if (e) return e; }
    if (s.additionalProperties === false) {
      for (const k of Object.keys(o)) if (!(s.properties && k in s.properties)) return `${at}.${k}: unknown argument`;
    }
  }
  return null;
}

// ---------------------------------------------------------------- tool contract (docs/interfaces/mcp-tools.json; a test compares them)
const PLANT_ID = { type: "string", format: "uuid" } as const;
const STATUS = ["ok", "dry", "wet", "low_battery", "offline", "no_device"] as const;
const ALERT_KINDS = ["too_dry", "too_wet", "low_battery", "device_offline", "wetting_unexpected", "waterlogged", "sensor_out_of_soil", "sensor_fault"] as const;
const READ_ONLY = { readOnlyHint: true, idempotentHint: true, openWorldHint: false };

export const TOOLS = [
  {
    name: "list_plants",
    description: "List the user's plants with current moisture, status and hours until the soil is dry. Use it to answer which plant needs water first (sort by hours_to_dry, then moisture_pct).",
    annotations: READ_ONLY,
    inputSchema: { type: "object", properties: {}, additionalProperties: false } as Schema,
    outputSchema: {
      type: "object", required: ["plants"],
      properties: {
        plants: {
          type: "array",
          items: {
            type: "object", required: ["plant_id", "name", "status"],
            properties: {
              plant_id: PLANT_ID, name: { type: "string" },
              location_type: { enum: ["house", "balcony", "garden", "farm", "greenhouse"] },
              area: { type: ["string", "null"] }, moisture_pct: { type: ["number", "null"] },
              hours_to_dry: { type: ["number", "null"] }, status: { enum: [...STATUS] },
              last_reading_at: { type: ["string", "null"], format: "date-time" },
            },
          },
        },
      },
    } as Schema,
  },
  {
    name: "get_plant_status",
    description: "Current state of one plant: latest values, thresholds, open alerts, forecast.",
    annotations: READ_ONLY,
    inputSchema: { type: "object", required: ["plant_id"], additionalProperties: false, properties: { plant_id: PLANT_ID } } as Schema,
    outputSchema: {
      type: "object", required: ["plant_id", "name", "status"],
      properties: {
        plant_id: PLANT_ID, name: { type: "string" }, species: { type: ["string", "null"] }, soil_type: { type: "string" },
        city: { type: ["string", "null"] }, status: { enum: [...STATUS] },
        reading_at: { type: ["string", "null"], format: "date-time" }, moisture_pct: { type: ["number", "null"] },
        temp_c: { type: ["number", "null"] }, rh_pct: { type: ["number", "null"] }, lux: { type: ["number", "null"] },
        battery_mv: { type: ["integer", "null"] }, dry_threshold_pct: { type: "number" }, wet_threshold_pct: { type: "number" },
        hours_to_dry: { type: ["number", "null"] },
        open_alerts: { type: "array", items: { enum: [...ALERT_KINDS] } },
      },
    } as Schema,
  },
  {
    name: "get_history",
    description: "Sensor history of one plant for charts and trends (up to 90 days, FR-P01). Plausible readings only.",
    annotations: READ_ONLY,
    inputSchema: {
      type: "object", required: ["plant_id"], additionalProperties: false,
      properties: {
        plant_id: PLANT_ID,
        days: { type: "integer", minimum: 1, maximum: 90, default: 7 },
        resolution: { enum: ["raw", "hourly", "daily"], default: "hourly" },
      },
    } as Schema,
    outputSchema: {
      type: "object", required: ["plant_id", "resolution", "points"],
      properties: {
        plant_id: PLANT_ID, resolution: { enum: ["raw", "hourly", "daily"] },
        points: {
          type: "array",
          items: {
            type: "object", required: ["ts"],
            properties: {
              ts: { type: "string", format: "date-time" }, moisture_pct: { type: ["number", "null"] },
              temp_c: { type: ["number", "null"] }, rh_pct: { type: ["number", "null"] }, lux: { type: ["number", "null"] },
              battery_mv: { type: ["integer", "null"] },
            },
          },
        },
        watering_events: { type: "array", items: { type: "string", format: "date-time" } },
      },
    } as Schema,
  },
  {
    name: "get_tips",
    description: "Current care tips for one plant (weather, season, plant and soil aware, passed through the safety rule layer). Returns cached tips if newer than their expiry, otherwise generates new ones.",
    annotations: { readOnlyHint: true, idempotentHint: false, openWorldHint: false },
    inputSchema: { type: "object", required: ["plant_id"], additionalProperties: false, properties: { plant_id: PLANT_ID } } as Schema,
    outputSchema: {
      type: "object", required: ["plant_id", "generated_at", "items"],
      properties: {
        plant_id: PLANT_ID, generated_at: { type: "string", format: "date-time" },
        items: {
          type: "array",
          items: {
            type: "object", required: ["id", "category", "text"],
            properties: { id: { type: "string" }, category: { enum: [...TIP_CATEGORIES] }, text: { type: "string", maxLength: TIP_TEXT_MAX } },
          },
        },
      },
    } as Schema,
  },
] as const;

// ---------------------------------------------------------------- plant status (FR-A06, FR-D06): row = a plant_status view row (migration 1), from mcp_list_plants / mcp_get_plant
export interface PlantRow {
  plant_id: string; name: string; location_type: string; area: string | null; species: string | null; soil_type: string;
  city: string | null; device_id: string | null; moisture_pct: number | null; temp_c: number | null; rh_pct: number | null;
  lux: number | null; vbat_mv: number | null; reading_ts: string | null; dry_threshold_pct: number; wet_threshold_pct: number;
  forecast_h: number | null; open_alerts: string[];
}
/** One status per plant, the most urgent first: no sensor, offline, low battery, too dry, too wet, otherwise ok. */
export function plantStatus(r: Pick<PlantRow, "device_id" | "open_alerts">): (typeof STATUS)[number] {
  if (!r.device_id) return "no_device";
  const a = new Set(r.open_alerts ?? []);
  if (a.has("device_offline")) return "offline";
  if (a.has("low_battery")) return "low_battery";
  if (a.has("too_dry")) return "dry";
  if (a.has("too_wet")) return "wet";
  return "ok";
}

// ---------------------------------------------------------------- results
type ToolResult = { content: { type: "text"; text: string }[]; structuredContent?: unknown; isError?: boolean };
const toolOk = (out: unknown): ToolResult => ({ content: [{ type: "text", text: JSON.stringify(out) }], structuredContent: out });
const toolError = (code: string, message?: string): ToolResult => ({
  content: [{ type: "text", text: JSON.stringify(message ? { error: code, message } : { error: code }) }], isError: true,
});
type Outcome = { ok: true; value: unknown } | { ok: false; code: string; message?: string };

/** Maps an SQL error text to a tool error code. Database messages are never passed on (only the code words the functions raise). */
function dbError(message: string): string {
  if (/premium_required/.test(message)) return "premium_required";
  if (/invalid_input/.test(message)) return "invalid_input";
  return "server_error";
}

// ---------------------------------------------------------------- authentication (FR-P03, NFR-06): runs before any read
type Auth = { ok: true; owner: string } | { ok: false; premium: boolean; response: Response };
const deny = (status: number, error: string, message: string): Auth => ({ ok: false, premium: false, response: err(status, error, message) });

export async function authenticate(req: Request, deps: McpDeps): Promise<Auth> {
  const key = bearer(req);
  if (!key || !KEY_PATTERN.test(key)) return deny(401, "unauthorized", "missing or malformed API key");
  // sha256(key) is the only form sent to the database (NFR-06); the key itself is never stored, logged or echoed.
  const r = await deps.rpc("mcp_resolve_key", { p_key_hash: `\\x${await sha256Hex(key)}` });
  if (r.error) {
    if (/premium_required/.test(r.error.message)) {
      return { ok: false, premium: true, response: err(403, "premium_required", "the MCP server is a premium feature (FR-P04)") };
    }
    return deny(500, "server_error", "key check failed");
  }
  // Unknown and revoked keys give the same answer: mcp_resolve_key returns null for both (FR-P03).
  if (typeof r.data !== "string" || !UUID_RE.test(r.data)) return deny(401, "key_revoked_or_unknown", "API key unknown or revoked");
  return { ok: true, owner: r.data };
}

// ---------------------------------------------------------------- tools (each reads only the key owner's rows)
async function callRpc(deps: McpDeps, name: string, args: Record<string, unknown>): Promise<Outcome> {
  const r = await deps.rpc(name, args);
  if (r.error) return { ok: false, code: dbError(r.error.message) };
  return { ok: true, value: r.data };
}

async function runTool(name: string, args: Record<string, unknown>, owner: string, deps: McpDeps): Promise<Outcome> {
  switch (name) {
    case "list_plants": {
      const o = await callRpc(deps, "mcp_list_plants", { p_owner: owner });
      if (!o.ok) return o;
      const rows = (Array.isArray(o.value) ? o.value : []) as PlantRow[];
      return { ok: true, value: { plants: rows.map((r) => ({
        plant_id: r.plant_id, name: r.name, location_type: r.location_type, area: r.area,
        moisture_pct: r.moisture_pct, hours_to_dry: r.forecast_h, status: plantStatus(r), last_reading_at: r.reading_ts,
      })) } };
    }
    case "get_plant_status": {
      const o = await callRpc(deps, "mcp_get_plant", { p_owner: owner, p_plant: args.plant_id });
      if (!o.ok) return o;
      if (o.value === null) return { ok: false, code: "not_found" };
      const r = o.value as PlantRow;
      return { ok: true, value: {
        plant_id: r.plant_id, name: r.name, species: r.species, soil_type: r.soil_type, city: r.city, status: plantStatus(r),
        reading_at: r.reading_ts, moisture_pct: r.moisture_pct, temp_c: r.temp_c, rh_pct: r.rh_pct, lux: r.lux,
        battery_mv: r.vbat_mv, dry_threshold_pct: r.dry_threshold_pct, wet_threshold_pct: r.wet_threshold_pct,
        hours_to_dry: r.forecast_h, open_alerts: r.open_alerts ?? [],
      } };
    }
    case "get_history": {
      const o = await callRpc(deps, "mcp_get_history", {
        p_owner: owner, p_plant: args.plant_id, p_days: args.days ?? 7, p_resolution: args.resolution ?? "hourly",
      });
      if (!o.ok) return o;
      if (o.value === null) return { ok: false, code: "not_found" };
      return { ok: true, value: o.value };
    }
    case "get_tips": {
      const o = await callRpc(deps, "mcp_get_tips", { p_owner: owner, p_plant: args.plant_id });
      if (!o.ok) return o;
      if (o.value === null) return { ok: false, code: "not_found" };
      const { tip } = o.value as { tip: { generated_at: string; content: unknown; guardrail_version: string } | null };
      // Read-only: no tip generation here. Missing, expired or other-version tips are refused, not regenerated.
      if (!tip) return { ok: false, code: "tips_unavailable", message: "no current tips yet" };
      if (tip.guardrail_version !== GUARDRAIL_VERSION_EXPECTED) return { ok: false, code: "tips_unavailable", message: "tips predate the current guardrails" };
      const items = (tip.content as { items?: unknown } | null)?.items;
      // Guardrail layer re-checked on the way out (FR-P02): any item outside the contract fails the whole answer.
      const itemSchema = TOOLS.find((t) => t.name === "get_tips")!.outputSchema.properties!.items.items!;
      if (!Array.isArray(items) || items.some((it) => validate(itemSchema, it) !== null)) {
        return { ok: false, code: "tips_unavailable", message: "stored tips failed the output check" };
      }
      return { ok: true, value: { plant_id: args.plant_id, generated_at: tip.generated_at, items } };
    }
    default:
      return { ok: false, code: "unknown_tool" };
  }
}

async function callTool(params: unknown, owner: string, deps: McpDeps): Promise<ToolResult> {
  const p = (typeof params === "object" && params !== null ? params : {}) as { name?: unknown; arguments?: unknown };
  const tool = TOOLS.find((t) => t.name === p.name);
  if (!tool) return toolError("unknown_tool");
  const args = p.arguments === undefined ? {} : p.arguments;
  if (typeof args !== "object" || args === null || Array.isArray(args)) return toolError("invalid_input", "arguments must be an object");
  const bad = validate(tool.inputSchema, args);
  if (bad) return toolError("invalid_input", bad);
  const input = args as Record<string, unknown>;
  const out = await runTool(tool.name, input, owner, deps);
  if (!out.ok) return toolError(out.code, out.message);
  // Output is checked against the contract before it leaves the server (fail closed: a shape mismatch is a server error).
  const shape = validate(tool.outputSchema, out.value);
  if (shape) return toolError("server_error", "output did not match the contract");
  return toolOk(out.value);
}

// ---------------------------------------------------------------- JSON-RPC over HTTP
const rpcResult = (id: unknown, result: unknown) => json(200, { jsonrpc: "2.0", id, result });
const rpcError = (id: unknown, code: number, message: string, status = 200) => json(status, { jsonrpc: "2.0", id, error: { code, message } });

export async function handleMcp(req: Request, deps: McpDeps): Promise<Response> {
  if (req.method !== "POST") return json(405, { error: "method_not_allowed" }, { allow: "POST" });
  const auth = await authenticate(req, deps);   // before the body is read: a bad key reads nothing
  if (!auth.ok && !auth.premium) return auth.response;

  const raw = await req.text();
  if (raw.length > MAX_BODY_BYTES) return err(413, "payload_too_large");
  let msg: unknown;
  try { msg = JSON.parse(raw); } catch { return rpcError(null, -32700, "parse error", 400); }
  if (typeof msg !== "object" || msg === null || Array.isArray(msg)) return rpcError(null, -32600, "invalid request", 400);
  const m = msg as { id?: unknown; method?: unknown; params?: unknown };
  if (typeof m.method !== "string") return rpcError(m.id ?? null, -32600, "invalid request", 400);
  const id = m.id ?? null;
  const notification = !("id" in (msg as object));

  // Free user (FR-P04): a tool call gets a clear tool error; any other method gets 403 premium_required.
  if (!auth.ok) {
    if (m.method === "tools/call") return rpcResult(id, toolError("premium_required"));
    return auth.response;
  }

  switch (m.method) {
    case "initialize":
      return rpcResult(id, { protocolVersion: PROTOCOL_VERSION, capabilities: { tools: {} }, serverInfo: SERVER_INFO });
    case "notifications/initialized":
      return new Response(null, { status: 202 });
    case "ping":
      return rpcResult(id, {});
    case "tools/list":
      return rpcResult(id, { tools: TOOLS.map((t) => ({ name: t.name, description: t.description, annotations: t.annotations, inputSchema: t.inputSchema, outputSchema: t.outputSchema })) });
    case "tools/call": {
      const result = await callTool(m.params, auth.owner, deps);
      return notification ? new Response(null, { status: 202 }) : rpcResult(id, result);
    }
    default:
      return notification ? new Response(null, { status: 202 }) : rpcError(id, -32601, "method not found");
  }
}

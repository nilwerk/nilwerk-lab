// Client for the care tips of one plant (task 4.A7). Reads public.tips through PostgREST with the user's JWT, as the other app reads do
// (plants/plantsRest.ts). Requirements: FR-P02 (the newest unexpired row; it is refused unless it is under the current guardrail version, and it is checked before it is shown),
// FR-P04 (the screen checks the plan first; the table policy tips_select_own_premium returns no rows to a free account), NFR-06 (RLS: own rows only).
// Same order as mcp_get_tips (cloud/supabase/migrations/20261123000010_mcp_read_rpcs.sql): the newest unexpired row of any guardrail version,
// then the version check (a newer row under another version is an error, never a silent fall back to an older row). The plant-ownership
// check that mcp_get_tips does in SQL is done by RLS here.
// NOT run against a live backend (no project exists, A-025); unit-tested with a fake fetch only.
import { parseTipsRow, type PlantTips } from './tipsModel';

export type TipsErrorCode = 'unauthorized' | 'network' | 'server' | 'bad_response' | 'unknown' | 'not_configured';

export class TipsError extends Error {
  code: TipsErrorCode;
  constructor(code: TipsErrorCode) {
    super(`tips: ${code}`);
    this.name = 'TipsError';
    this.code = code;
  }
}

export interface TipsService {
  /** Resolves with the newest current tips, or null when there are none yet. Rejects with TipsError. */
  fetchPlantTips(plantId: string): Promise<PlantTips | null>;
}

export interface TipsClientDeps {
  baseUrl: string;
  publishableKey: string;
  getAccessToken: () => Promise<string | null>;
  fetchImpl?: typeof fetch;
  /** Clock used for the expiry filter; tests pass a fixed value. */
  now?: () => Date;
}

export const tipsUrl = (baseUrl: string, plantId: string, nowIso: string): string => {
  const q = new URLSearchParams({
    select: 'generated_at,content,guardrail_version',
    plant_id: `eq.${plantId}`,
    expires_at: `gt.${nowIso}`,
    order: 'generated_at.desc',
    limit: '1',
  });
  return `${baseUrl.replace(/\/+$/, '')}/rest/v1/tips?${q.toString()}`;
};

export function createTipsClient(d: TipsClientDeps): TipsService {
  return {
    async fetchPlantTips(plantId) {
      const token = await d.getAccessToken().catch(() => null);
      if (!token) throw new TipsError('unauthorized');
      const url = tipsUrl(d.baseUrl, plantId, (d.now ?? (() => new Date()))().toISOString());
      let res: Response;
      try {
        res = await (d.fetchImpl ?? fetch)(url, {
          method: 'GET',
          headers: { Authorization: `Bearer ${token}`, apikey: d.publishableKey, Accept: 'application/json' },
        });
      } catch {
        throw new TipsError('network');
      }
      if (res.status === 401) throw new TipsError('unauthorized');
      if (res.status >= 500) throw new TipsError('server');
      if (res.status !== 200) throw new TipsError('unknown');
      let json: unknown;
      try { json = await res.json(); } catch { throw new TipsError('bad_response'); }
      if (!Array.isArray(json)) throw new TipsError('bad_response');
      if (json.length === 0) return null;
      const tips = parseTipsRow(json[0], plantId);
      if (!tips) throw new TipsError('bad_response');
      return tips.items.length === 0 ? null : tips;
    },
  };
}

/** Used when no backend is configured: every call reports not_configured and nothing is fetched. */
export const unconfiguredTips: TipsService = {
  fetchPlantTips: async () => { throw new TipsError('not_configured'); },
};

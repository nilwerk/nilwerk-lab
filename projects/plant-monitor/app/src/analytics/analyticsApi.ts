// Client for GET /analytics?window=30|90 (task 4.A6 consumes 4.B4). Requirements: FR-P01, FR-P04 (403 premium_required is shown as the upgrade state),
// NFR-06 (the user's JWT is sent; the server only returns the caller's rows). Route: the edge function is in the repo (4.B4, 4.B4b) but not deployed,
// so the URL below is a proposed path and is unverified until a deployed function returns `daily` (docs/interfaces/openapi.yaml /analytics).
// Unit-tested with a fake fetch only. No live call is made from tests.
import { parseAnalyticsResponse, type AnalyticsResponse, type AnalyticsWindow } from './analyticsModel';

export type AnalyticsErrorCode = 'premium_required' | 'unauthorized' | 'network' | 'server' | 'bad_response' | 'not_configured' | 'unknown';

export class AnalyticsError extends Error {
  code: AnalyticsErrorCode;
  constructor(code: AnalyticsErrorCode) {
    super(`analytics: ${code}`);
    this.name = 'AnalyticsError';
    this.code = code;
  }
}

export interface AnalyticsService {
  fetchWindow(windowDays: AnalyticsWindow): Promise<AnalyticsResponse>;
}

export interface AnalyticsClientDeps {
  baseUrl: string;
  publishableKey: string;
  getAccessToken: () => Promise<string | null>;
  fetchImpl?: typeof fetch;
}

export const analyticsUrl = (baseUrl: string, windowDays: AnalyticsWindow): string =>
  `${baseUrl.replace(/\/+$/, '')}/functions/v1/analytics?window=${windowDays}`;

export function createAnalyticsClient(d: AnalyticsClientDeps): AnalyticsService {
  return {
    async fetchWindow(windowDays) {
      const token = await d.getAccessToken().catch(() => null);
      if (!token) throw new AnalyticsError('unauthorized');
      let res: Response;
      try {
        res = await (d.fetchImpl ?? fetch)(analyticsUrl(d.baseUrl, windowDays), {
          method: 'GET',
          headers: { Authorization: `Bearer ${token}`, apikey: d.publishableKey, Accept: 'application/json' },
        });
      } catch {
        throw new AnalyticsError('network');
      }
      if (res.status === 403) throw new AnalyticsError('premium_required');
      if (res.status === 401) throw new AnalyticsError('unauthorized');
      if (res.status >= 500) throw new AnalyticsError('server');
      if (res.status !== 200) throw new AnalyticsError('unknown');
      let json: unknown;
      try { json = await res.json(); } catch { throw new AnalyticsError('bad_response'); }
      const parsed = parseAnalyticsResponse(json, windowDays);
      if (!parsed) throw new AnalyticsError('bad_response');
      return parsed;
    },
  };
}

/** Used when no backend is configured (or in the mock build): every call reports not_configured, nothing is fetched. */
export const unconfiguredAnalytics: AnalyticsService = {
  fetchWindow: async () => { throw new AnalyticsError('not_configured'); },
};

// Client for DELETE /account (edge function `delete-account`, project nilwerk-cloud). Contract: docs/interfaces/openapi.yaml /account.
// Requirements: FR-A01 (delete account), NFR-07 (deletion removes all data), NFR-06 (only the token's own user can be deleted: the body carries no user id).
// The base URL and the publishable key come from the build config (src/config.ts <- app.config.ts <- SUPABASE_URL / SUPABASE_PUBLISHABLE_KEY), never from code.
export type AccountApiErrorCode = 'unauthorized' | 'network' | 'bad_request' | 'server' | 'unknown';

export class AccountApiError extends Error {
  code: AccountApiErrorCode;
  status?: number;
  constructor(code: AccountApiErrorCode, status?: number) {
    super(status ? `DELETE /account: ${code} (${status})` : `DELETE /account: ${code}`);
    this.name = 'AccountApiError';
    this.code = code;
    this.status = status;
  }
}

export interface DeleteAccountRequest {
  baseUrl: string;
  publishableKey: string;
  /** the signed-in user's JWT; the function verifies it itself (verify_jwt = false, auth.getUser) */
  accessToken: string;
  fetchImpl?: typeof fetch;
}

/** The function's route is /functions/v1/delete-account (the OpenAPI path /account is the logical name, not the URL). */
export const deleteAccountUrl = (baseUrl: string): string => `${baseUrl.replace(/\/+$/, '')}/functions/v1/delete-account`;

/** Resolves on 204. Rejects with AccountApiError: 401 unauthorized, 400/405/413 bad_request, 5xx server, fetch failure network, anything else unknown. */
export async function deleteAccountApi({ baseUrl, publishableKey, accessToken, fetchImpl = fetch }: DeleteAccountRequest): Promise<void> {
  if (!accessToken) throw new AccountApiError('unauthorized');
  let res: Response;
  try {
    res = await fetchImpl(deleteAccountUrl(baseUrl), {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${accessToken}`, apikey: publishableKey, 'Content-Type': 'application/json' },
      body: JSON.stringify({ confirm: 'DELETE' }),
    });
  } catch {
    throw new AccountApiError('network');
  }
  if (res.status === 204) return;
  if (res.status === 401) throw new AccountApiError('unauthorized', 401);
  if (res.status === 400 || res.status === 405 || res.status === 413) throw new AccountApiError('bad_request', res.status);
  if (res.status >= 500) throw new AccountApiError('server', res.status);
  throw new AccountApiError('unknown', res.status);
}

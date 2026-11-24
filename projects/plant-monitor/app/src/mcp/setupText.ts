// Copy-paste setup text for MCP clients (task 4.A8). Requirements: FR-P03 (connect the user's own AI to their plant data).
// Placeholders only: no real key and no real host ever appears here. The user pastes their own key and the server address.
// Server name, transport and header format come from docs/interfaces/mcp-tools.json (Streamable HTTP, "Authorization: Bearer nwk_<key>").
export const MCP_SERVER_NAME = 'nilwerk-plant-monitor';
export const URL_PLACEHOLDER = '<MCP_SERVER_URL>';
export const KEY_PLACEHOLDER = '<YOUR_API_KEY>';

/** Claude Code (command line). */
export const claudeSetupText = (): string =>
  `claude mcp add --transport http ${MCP_SERVER_NAME} ${URL_PLACEHOLDER} --header "Authorization: Bearer ${KEY_PLACEHOLDER}"`;

/** Any other MCP client that takes a JSON server entry with a URL and headers. */
export const genericSetupText = (): string =>
  JSON.stringify({ mcpServers: { [MCP_SERVER_NAME]: { type: 'http', url: URL_PLACEHOLDER, headers: { Authorization: `Bearer ${KEY_PLACEHOLDER}` } } } }, null, 2);

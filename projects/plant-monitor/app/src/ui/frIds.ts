// Requirement IDs each screen implements (playbook: every requirement implemented cites its ID). Tested in __tests__/screens.test.tsx.
// Screen codes follow app/wireframes/index.html (S01..S04, S40).
export const SCREEN_FR = {
  welcome: ['FR-A01'],                       // S01 Welcome
  signUp: ['FR-A01'],                        // S02 Sign up (auth.users.email, profiles.display_name)
  signIn: ['FR-A01'],                        // S02 Sign in
  profile: ['FR-A01', 'FR-P04', 'NFR-06'],   // S03 Profile (plan mirrors profiles.is_premium; own row only under RLS)
  deleteAccount: ['FR-A01', 'NFR-07'],       // S04 Delete account (DELETE /account, 0 rows remain)
  plants: ['FR-A06', 'FR-A02', 'NFR-06'],     // S20 Plant list with status chips (no device cap)
  plantDetail: ['FR-A06', 'FR-A04', 'FR-A08', 'FR-P02', 'FR-P04', 'NFR-06'],  // S21 Plant detail: latest values, 7-day chart + hourly table (FR-D02 in HourlyTable), metadata (FR-A04), entry to photos, care tips (FR-P02, FR-P04) and remove
  plantGallery: ['FR-A05', 'NFR-06'],         // S23 Photo gallery: unlimited dated photos, newest/oldest first
  removePlant: ['FR-A08', 'A-022', 'NFR-07'],   // S24b/S24c Remove plant (delete_plant), keep/release sensor
  setup: ['FR-A03', 'FR-D03', 'FR-A04', 'FR-A05', 'NFR-03'], // S10-S16 device setup (A-023: no hub step); FR-D02/D07/A02 also cited in SetupSteps
  premium: ['FR-P04'],                       // S40 Premium sheet (A-024: activated by Nilwerk + contact link)
  premiumDashboard: ['FR-P01', 'FR-P04', 'NFR-06'], // S41 Premium dashboard (4.A6): 30/90-day aggregates, trends, watering events; upgrade state for free accounts
  connectAi: ['FR-P03', 'FR-P04', 'NFR-06'], // S42 Connect your AI (4.A8): create (shown once) / revoke an MCP key, setup text; locked state for free accounts
  plantTips: ['FR-P02', 'FR-P04', 'NFR-06'],  // Care tips (4.A7): stored guardrailed tips of one plant; upgrade state for free accounts
  alerts: ['FR-A07', 'FR-D06', 'FR-A06'],    // S30 Alerts list (4.A5): rules in plants/alerts.ts; push delivery not built, S31 detail not built
} as const;

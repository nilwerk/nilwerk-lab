// Requirement IDs each screen implements (playbook: every requirement implemented cites its ID). Tested in __tests__/screens.test.tsx.
// Screen codes follow app/wireframes/index.html (S01..S04, S40).
export const SCREEN_FR = {
  welcome: ['FR-A01'],                       // S01 Welcome
  signUp: ['FR-A01'],                        // S02 Sign up (auth.users.email, profiles.display_name)
  signIn: ['FR-A01'],                        // S02 Sign in
  profile: ['FR-A01', 'FR-P04', 'NFR-06'],   // S03 Profile (plan mirrors profiles.is_premium; own row only under RLS)
  deleteAccount: ['FR-A01', 'NFR-07'],       // S04 Delete account (DELETE /account, 0 rows remain)
  plants: ['FR-A06', 'FR-A02', 'NFR-06'],     // S20 Plant list with status chips (no device cap)
  plantDetail: ['FR-A06', 'FR-A07', 'FR-A08'],  // S21 Plant detail: latest values, 7-day chart, thresholds, entry to remove
  removePlant: ['FR-A08', 'A-022', 'NFR-07'],   // S24b/S24c Remove plant (delete_plant), keep/release sensor
  premium: ['FR-P04'],                       // S40 Premium sheet (A-024: activated by Nilwerk + contact link)
} as const;

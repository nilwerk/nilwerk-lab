// Requirement IDs each screen implements (playbook: every requirement implemented cites its ID). Tested in __tests__/screens.test.tsx.
// Screen codes follow app/wireframes/index.html (S01..S04, S40).
export const SCREEN_FR = {
  welcome: ['FR-A01'],                       // S01 Welcome
  signUp: ['FR-A01'],                        // S02 Sign up (auth.users.email, profiles.display_name)
  signIn: ['FR-A01'],                        // S02 Sign in
  profile: ['FR-A01', 'FR-P04', 'NFR-06'],   // S03 Profile (plan mirrors profiles.is_premium; own row only under RLS)
  deleteAccount: ['FR-A01', 'NFR-07'],       // S04 Delete account (DELETE /account, 0 rows remain)
  premium: ['FR-P04'],                       // S40 Premium sheet (A-024: activated by Nilwerk + contact link)
} as const;

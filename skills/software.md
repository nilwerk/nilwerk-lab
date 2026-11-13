# Software skills — app, backend, cloud, ML, MCP

| Name | What | URL | Status | Used by |
|---|---|---|---|---|
| Expo docs | Official home page verified. Development builds (needed for BLE) are NOT on the home page: find the dev-build page under docs.expo.dev and verify it | https://docs.expo.dev | verified 13 Nov (Lead fetch) (home); dev-build page to verify | Leo |
| React Native | App framework | https://reactnative.dev | to verify | Leo |
| Supabase Auth | Sign-up, sign-in, deletion | https://supabase.com/docs/guides/auth | to verify | Leo, Sana |
| Supabase Row Level Security | RLS on every table (NFR-06). Verified points: enable RLS on each table; with no policy the API returns no rows; revoke default grants to anon and authenticated; one policy per operation; test with pgTAP and `supabase test db` | https://supabase.com/docs/guides/database/postgres/row-level-security | verified 13 Nov (Lead fetch) | Leo, Sana, Ines |
| Supabase Edge Functions | Ingest, claim, delete-account | https://supabase.com/docs/guides/functions | to verify | Sana |
| Supabase cron (pg_cron) | Scheduled roll-ups | https://supabase.com/docs/guides/cron | to verify | Sana |
| Deno manual | Edge runtime, lint, typecheck | https://deno.com/manual | to verify | Sana |
| Model Context Protocol spec | MCP tool schemas; latest spec dated 2026-07-28 | https://modelcontextprotocol.io/specification | verified 13 Nov (Lead fetch) | Sana |
| react-native-ble-plx | BLE in the app | https://github.com/dotintent/react-native-ble-plx | to verify | Leo |
| BLE provisioning plugin | `@orbital-systems/react-native-esp-idf-provisioning` (needs a dev build) | URL to find and verify | to verify | Leo |
| scikit-learn, TensorFlow (Python) | ML under `ml/` | https://scikit-learn.org, https://www.tensorflow.org | to verify | Sana, Mira |
| Playwright | App end-to-end tests | https://playwright.dev | to verify | Ines |
| pytest | Python tests (edge AI, tools); pytest 9.x, Python 3.10+ | https://docs.pytest.org | verified 13 Nov (Lead fetch) | Ines, Sana |

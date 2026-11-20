# App alerts list (mock readings): too dry, too wet, low battery, offline

**What it shows.** The app's alerts list, opened from the plant list, running in a headless browser on the mock build at phone width (390 px). The alert rules run on fixed test readings and list four alert kinds for three of the five mock plants. Every screen carries a MOCK label. Push notifications are not built: the list is the only place alerts show.

**Task.** 4.A5, "App: alerts" (slice: alerts list and alert rules). Not in this slice: push delivery, edge-AI events (wetting, out of soil, sensor fault), the alert detail screen.

**Persona.** Full-stack agent (app front end).

**Images.** The repo holds no images, so the screenshot is not committed. It is at `/home/user/sim-evidence/app/06-alerts.png` (outside the repo), 390 px wide, scale 1. Upload it to Drive `Nilwerk/Marketing/Assets/` if it is used publicly.

**Time.** Agent minutes:  (wall clock, 19:36:15 to 2026-11-20 19:42:36 CET). Own human estimate for an experienced engineer: about 6 h.

**Unverified.** Real push notifications and their no-duplicate rule, real Bluetooth, real sensors, live Supabase data, a phone build (not run on a phone). The app works on hourly averages, while the server works on raw 15-minute samples, so edge cases can differ. The 5-point clear margin and the battery clear level are still marked to confirm in the code.

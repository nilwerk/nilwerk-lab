# Wireframe palette (Leo, A-024 proposal) vs brand tokens: differences and ONE aligned set

Read: `projects/plant-monitor/app/wireframes/index.html` (section "Brand: name, palette, icon concept") and the screens (e.g. `03-plants.png`). The wireframes are **not changed** by this task. Leo wrote that "all screens use tokens only (4.A2 theme file)", so the alignment below is a matter of which values 4.A2 puts in `theme.ts`.

## Differences

| Token (Leo) | Leo light / dark | Brand token | Brand light / dark | Contrast note (computed, text on his bg / card) |
|---|---|---|---|---|
| `--bg` app background | `#F5F8F6` / `#171B18` (cool grey-green) | `bg` | `#F6F4EF` / `#101317` (warm paper / blue-black) | both fine; the brand bg matches nilwerk.de and the posts |
| `--fg` text | `#1D2420` / `#E8ECE9` | `ink` | `#15181D` / `#ECEBE7` | both fine (14.8 vs 16.2 on bg) |
| `--mut` secondary text | `#6B756E` / `#9AA59D` | `muted` | `#5B616B` / `#A2A7AF` | **Leo light 4.47:1 on bg is just below AA (4.5)**; brand 5.67 |
| `--pri` primary | `#1E7F5C` / `#4CB48A` | `accent` | `#0F7A5C` / `#3FC79A` | similar hue; Leo light 4.63, brand 4.83. **Leo dark: white text on `#4CB48A` is only 2.56:1**; brand uses dark ink on the accent (`accent-ink` `#0C1512`, 8.70) |
| `--card` | `#FFFFFF` / `#222823` | `surface` | `#FFFFFF` / `#181C22` | fine |
| water (moisture) | `#2B7BB9` / `#6DB3E8` | `wet` | `#1F6AA5` / `#6DB3E8` | **Leo light 4.24 on bg fails AA** for text; brand wet 5.22 |
| warn (low battery, offline) | `#C98A00` / `#E0A93A` | `low` (low battery), `offline` (offline) | `#8A5D00` / `#E0A93A`; `#5B616B` / `#A2A7AF` | **Leo light amber 2.76:1 fails AA**; offline gets its own neutral status |
| danger (too dry/wet, delete) | `#C0392B` / `#E27163` | `danger` (error, delete), `dry` (needs water), `wet` (too wet) | `#B3261E` / `#E27163`; `#B4541A` / `#E58A4F`; `#1F6AA5` / `#6DB3E8` | Leo uses one red for too dry and too wet; the brand set separates dry (orange), wet (blue) and error (red) so colour-blind users and screenshots read better, always with a word and a shape |
| App icon concept | white leaf on a green rounded square, small water drop (Leo, A-024) | existing logo mark | dark plate, green trace-N, pads, wave | brand mark proposed (existing logo, one identity); Leo's concept was "final artwork is a 4.A2 task" |
| Fonts | system sans + monospace (wireframes) | Space Grotesk / Inter / JetBrains Mono | via `@expo-google-fonts/*` | wireframes are low-fidelity, so no conflict |
| Language | English only, strings from `app/strings/en.json` | status labels | keys `status.ok`, `status.dry`, `status.wet`, `status.lowBattery`, `status.offline`, `status.error` | **these keys do not exist in `en.json` yet**; 4.A2 adds them (text proposal: OK, Too dry, Too wet, Low battery, Offline, Error) |

## Proposed ONE aligned set (what `theme.ts` / `tokens.json` contain)

Brand tokens for background, text, muted, primary and surfaces; the status set in `../brand-status.css` for plant states (dry, wet, low battery, offline, error, ok); dark text on the accent in dark mode; icon from the existing mark. It keeps Leo's idea (one token file, no hard-coded colours) and his status meanings, and fixes the AA failures above. All pairs are checked by `../check_status_contrast.py` (exit 0).

Leo's token names map as: `bg`→`color.bg`, `fg`→`color.ink`, `mut`→`color.muted`, `card`→`color.surface`, `line`→`color.line`, `pri`→`color.accent`, `on`→`color.accentSoft`, `bad`→`color.danger`, `warn`→`color.low` (battery) / `color.offline` (offline), water→`color.wet`.

## Needs a decision (listed in the task result for Arsany)

Adopt this aligned set for the app (4.A2), and the brand mark as app icon instead of the leaf-and-drop concept. If not, the wireframe palette stays and its AA failures (light muted, water, amber) remain to be fixed by Leo.

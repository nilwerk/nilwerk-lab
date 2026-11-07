> **Internal working document, not for publication.** It compares the app wireframes with the brand tokens for Leo and Theo (4.A2). Do not copy it into posts, slides or the website.

# Wireframe palette (Leo's proposal) vs brand tokens: differences and ONE aligned set

Read: `projects/plant-monitor/app/wireframes/index.html` (section "Brand: name, palette, icon concept") and the screens (e.g. `03-plants.png`). The wireframes are **not changed** by this task. Leo wrote that "all screens use tokens only (4.A2 theme file)", so the alignment below is a matter of which values 4.A2 puts in `theme.ts`.

Contrast is computed per surface. In the wireframes, body and secondary text sit on `--card` (white / `#222823`) inside cards and on `--bg` on the page background; buttons are white (light) text on `--pri`.

## Differences

| Token (Leo) | Leo light / dark | Brand token | Brand light / dark | Contrast (computed) |
|---|---|---|---|---|
| `--bg` app background | `#F5F8F6` / `#171B18` (cool grey-green) | `bg` | `#F6F4EF` / `#101317` (warm paper / blue-black) | no problem; the brand bg matches nilwerk.de and the posts |
| `--fg` text | `#1D2420` / `#E8ECE9` | `ink` | `#15181D` / `#ECEBE7` | fine on both surfaces (14.8 on bg, 15.8 on card) |
| `--mut` secondary text | `#6B756E` / `#9AA59D` | `muted` | `#5B616B` / `#A2A7AF` | on `--card` white **4.78 passes**; on `--bg` **4.47 is marginally below 4.5**. Brand: 5.67 on bg, 6.24 on surface |
| `--pri` primary | `#1E7F5C` / `#4CB48A` | `accent` | `#0F7A5C` / `#3FC79A` | text on bg 4.63, on card 4.95 (pass). **Dark mode: white button text on `#4CB48A` is 2.56:1, a real failure**; the brand uses dark ink on the accent (`accent-ink` `#0C1512`, 8.70) |
| `--card` | `#FFFFFF` / `#222823` | `surface` | `#FFFFFF` / `#181C22` | fine |
| water (moisture) | `#2B7BB9` / `#6DB3E8` | `wet` | `#1F6AA5` / `#6DB3E8` | on `--card` white **4.53 passes** (barely); on `--bg` **4.24 is marginally below AA**. Brand: 5.22 on bg, 5.73 on surface |
| warn (low battery, offline) | `#C98A00` / `#E0A93A` | `low` (low battery), `offline` (offline) | `#8A5D00` / `#E0A93A`; `#5B616B` / `#A2A7AF` | **light amber on card 2.95 and on bg 2.76 is a real failure for text**; dark is fine (7.1 on card). Offline gets its own neutral status |
| danger (too dry/wet, delete) | `#C0392B` / `#E27163` | `danger` (error, delete), `dry` (needs water), `wet` (too wet) | `#B3261E` / `#E27163`; `#B4541A` / `#E58A4F`; `#1F6AA5` / `#6DB3E8` | Leo's red passes (5.09 / 5.44). Leo uses one red for too dry and too wet; the brand set separates dry (orange), wet (blue) and error (red) so colour-blind users and screenshots read better, always with a word and a shape |
| App icon concept | white leaf on a green rounded square, small water drop (Leo) | existing logo mark | dark plate, green trace-N, pads, wave | brand mark proposed (existing logo, one identity); Leo wrote "final artwork is a 4.A2 task" |
| Fonts | system sans + monospace (wireframes) | Space Grotesk / Inter / JetBrains Mono | via `@expo-google-fonts/*` | wireframes are low-fidelity, so no conflict |
| Language | English only, strings from `app/strings/en.json` | status labels | keys `status.ok`, `status.dry`, `status.wet`, `status.lowBattery`, `status.offline`, `status.error` | **these keys do not exist in `en.json` yet**; 4.A2 adds them (text proposal: OK, Too dry, Too wet, Low battery, Offline, Error) |

## Proposed ONE aligned set (what `theme.ts` / `tokens.json` contain)

Brand tokens for background, text, muted, primary and surfaces; the status set in `../brand-status.css` for plant states (dry, wet, low battery, offline, error, ok); dark text on the accent in dark mode; icon from the existing mark. It keeps Leo's idea (one token file, no hard-coded colours) and his status meanings, removes the two real failures (amber text in light mode, white on dark green in dark mode) and gives the marginal pairs (muted and water on `--bg`) comfortable headroom. All brand pairs are checked by `../check_status_contrast.py` (exit 0).

Leo's token names map as: `bg`→`color.bg`, `fg`→`color.ink`, `mut`→`color.muted`, `card`→`color.surface`, `line`→`color.line`, `pri`→`color.accent`, `on`→`color.accentSoft`, `bad`→`color.danger`, `warn`→`color.low` (battery) / `color.offline` (offline), water→`color.wet`.

## Decision for Arsany (listed in the task result)

Adopt this aligned set for the app (4.A2), and the brand mark as app icon instead of the leaf-and-drop concept. If not, the wireframe palette stays and Leo fixes the two real failures (light amber text, white on dark green) and the marginal muted/water pairs on `--bg`.

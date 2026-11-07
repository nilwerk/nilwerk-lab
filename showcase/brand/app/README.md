# Mobile app brand kit (React Native / Expo), v0.1 brand, proposal

For both audiences: people who just want to know "is my plant OK?" (plain words, big status, one action) and technical users (exact numbers in mono, sensor details on a second level, same tokens).

| File | What |
|---|---|
| `theme.ts` | typed theme: colours light/dark, spacing, radii, typography scale, status colours, `getTheme(scheme)`, `statusStyle(status, scheme)` (scheme accepts `string \| null \| undefined`). Pure TypeScript (`tsc --noEmit` passes, strict) |
| `tokens.json` | the same tokens as data (for tooling, Figma tokens, tests) |
| `tsconfig.json` | strict, noEmit config used for the check |
| `assets/icon-1024.png` | app icon (opaque RGB, dark ink, mark at 60 %), source `.svg` |
| `assets/adaptive-icon-foreground-1024.png` | Android adaptive icon foreground: **RGBA with real transparency** (PNG colour type 6, corner pixel alpha 0), mark inside the 66 % safe zone |
| `assets/splash-light-1284x2778.png`, `splash-dark-...` | splash images (mark plate + wordmark, centred, opaque) |
| `assets/favicon-48.png` | web favicon |
| `WIREFRAME-MAPPING.md` | internal note: differences to Leo's wireframe palette and the proposed aligned set |
| `make_app_assets.py` | regenerates everything above from `../brand.css` + `../brand-status.css` (single source) |

## Wiring into Expo (`app.json`, for 4.A2)

**4.A2 must confirm every key below against the current Expo SDK**: the config names and plugin options change between SDK versions, and none of this was run in an Expo app.

```json
{
  "expo": {
    "icon": "./assets/icon-1024.png",
    "userInterfaceStyle": "automatic",
    "android": { "adaptiveIcon": { "foregroundImage": "./assets/adaptive-icon-foreground-1024.png", "backgroundColor": "#15181d" } },
    "web": { "favicon": "./assets/favicon-48.png" },
    "plugins": [
      ["expo-splash-screen", {
        "image": "./assets/splash-light-1284x2778.png",
        "backgroundColor": "#f6f4ef",
        "imageWidth": 200,
        "dark": { "image": "./assets/splash-dark-1284x2778.png", "backgroundColor": "#101317" }
      }]
    ]
  }
}
```

The splash is configured **only** through the `expo-splash-screen` plugin (light and dark), not through a top-level `splash` key. Copy `theme.ts`, `tokens.json` and `assets/` into the app.

Fonts (install `expo-font` and the three `@expo-google-fonts/*` packages, see the comment in `theme.ts`):

```ts
import { useFonts } from 'expo-font';
import { SpaceGrotesk_500Medium, SpaceGrotesk_700Bold } from '@expo-google-fonts/space-grotesk';
import { Inter_400Regular, Inter_600SemiBold } from '@expo-google-fonts/inter';
import { JetBrainsMono_400Regular, JetBrainsMono_600SemiBold } from '@expo-google-fonts/jetbrains-mono';
const [loaded] = useFonts({ SpaceGrotesk_500Medium, SpaceGrotesk_700Bold, Inter_400Regular, Inter_600SemiBold, JetBrainsMono_400Regular, JetBrainsMono_600SemiBold });
// render the splash / nothing until `loaded` is true
```

## Status colours (dry, wet, low battery, offline)

| Status | Colour (light / dark) | Shape | Label key | Use |
|---|---|---|---|---|
| ok | `#0f7a5c` / `#3fc79a` | circle | `status.ok` | plant within thresholds |
| dry | `#b4541a` / `#e58a4f` | triangle | `status.dry` | below the dry threshold, needs water |
| wet | `#1f6aa5` / `#6db3e8` | diamond | `status.wet` | above the wet threshold |
| lowBattery | `#8a5d00` / `#e0a93a` | square | `status.lowBattery` | battery below the low-battery warning |
| offline | `#5b616b` / `#a2a7af` | ring | `status.offline` | no recent report |
| error | `#b3261e` / `#e27163` | cross | `status.error` | failures, destructive actions |

Rules: never colour alone (label + shape); touch targets at least 44 pt; text sizes from the typography scale; body text on `bg` or `surface` only; status colour as text only on its own soft background or on `bg` / `surface` (all pairs AA, see `../check_status_contrast.py`).

## Alerts to statuses (FR-A07)

Thresholds, clear rules and timing (for example the low-battery level and when it clears, the offline delay) are defined once in `projects/plant-monitor/docs/requirements-v1.0-delta.md`, row **FR-A07**. They are not repeated here; read them there.

| `alerts.kind` (db schema) | `PlantStatus` | Note |
|---|---|---|
| `too_dry` | `dry` | |
| `too_wet` | `wet` | |
| `low_battery` | `lowBattery` | |
| `device_offline` | `offline` | |
| (no open alert) | `ok` | `ok` is the absence of an open alert |
| `wetting_unexpected`, `waterlogged`, `sensor_out_of_soil`, `sensor_fault` | **open decision for Leo / 4.A2: use the `error` key or add a new key** | not decided here; these are the edge-AI critical kinds listed in FR-A07 |

**Priority when several alerts are open (proposal, not decided):** show one badge per plant on the list, the highest of: `offline` (data is stale, other states are unreliable) > `error` / edge-AI kinds > `dry` / `wet` > `lowBattery` > `ok`; the plant detail screen lists all open alerts. Leo / 4.A2 decide.

## Audiences in the app

- **Non-technical:** list shows plant name, one status badge in words ("Too dry"), and one plain sentence ("Water it today"); no units jargon.
- **Technical:** plant detail shows the numbers in `number` / `label` mono styles (38 %, 21.4 °C, 3.82 V, firmware version), and the status thresholds. Same colours, deeper layer.

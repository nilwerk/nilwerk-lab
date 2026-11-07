# Mobile app brand kit (React Native / Expo), v0.1 brand, proposal

For both audiences: people who just want to know "is my plant OK?" (plain words, big status, one action) and technical users (exact numbers in mono, sensor details on a second level, same tokens).

| File | What |
|---|---|
| `theme.ts` | typed theme: colours light/dark, spacing, radii, typography scale, status colours, `getTheme(scheme)`, `statusStyle(status, scheme)`. Pure TypeScript (`tsc --noEmit` passes with TypeScript 6.0.2, strict) |
| `tokens.json` | the same tokens as data (for tooling, Figma tokens, tests) |
| `tsconfig.json` | strict, noEmit config used for the check |
| `assets/icon-1024.png` | app icon (opaque, dark ink, mark at 60 %), source `.svg` |
| `assets/adaptive-icon-foreground-1024.png` | Android adaptive icon foreground (transparent, inside the 66 % safe zone) |
| `assets/splash-light-1284x2778.png`, `splash-dark-...` | splash images (mark plate + wordmark, centred) |
| `assets/favicon-48.png` | web favicon |
| `WIREFRAME-MAPPING.md` | differences to Leo's wireframe palette and the proposed aligned set |
| `make_app_assets.py` | regenerates everything above from `../brand.css` + `../brand-status.css` (single source) |

## Wiring into Expo (`app.json`, for 4.A2)

```json
{
  "expo": {
    "icon": "./assets/icon-1024.png",
    "userInterfaceStyle": "automatic",
    "splash": { "image": "./assets/splash-light-1284x2778.png", "resizeMode": "contain", "backgroundColor": "#f6f4ef" },
    "android": { "adaptiveIcon": { "foregroundImage": "./assets/adaptive-icon-foreground-1024.png", "backgroundColor": "#15181d" } },
    "web": { "favicon": "./assets/favicon-48.png" }
  }
}
```
(Copy `theme.ts`, `tokens.json` and `assets/` into the app. A dark splash needs the `expo-splash-screen` plugin's `dark` option with `splash-dark-1284x2778.png` and `#101317`.)

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

## Audiences in the app

- **Non-technical:** list shows plant name, one status badge in words ("Too dry"), and one plain sentence ("Water it today"); no units jargon.
- **Technical:** plant detail shows the numbers in `number` / `label` mono styles (38 %, 21.4 °C, 3.82 V, firmware version), and the status thresholds. Same colours, deeper layer.

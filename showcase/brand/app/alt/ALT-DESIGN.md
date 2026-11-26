# Alternative app design: "The clear path" (My plants, plant detail, setup)

Status: **draft, design only, no app code changed.** Owner: UI/UX Designer (Lena, NW-UX-13). Her role file is still pending Arsany's approval, so treat this as a proposal for review, not a shipped direction.
Builds on: `projects/plant-monitor/docs/design/app-design-review-2026-11-25.md` (principles P1 to P9) and the v3 structure in `showcase/brand/app/V3-PROPOSAL.md` (PR #235).
Mockup: `alt-mockup.html` in this folder (mock data only, tokens from `projects/plant-monitor/app/tokens.json`).

## 1. What is different from v3

v3 fixes structure. This alternative changes **what the user does next**, so each screen has one clear action in view.

| Screen | v3 (PR #235) | Alternative | Principle |
|---|---|---|---|
| My plants | Needs-attention strip above the list | A single "Needs water" card at the top with one filled action that opens the first plant that needs it. Rows keep the status chip and gain a moisture meter with dry and wet limits marked. | P1, P2, P7 |
| Plant detail | Hero number, then chart, then grid | Hero number, one plain next-step sentence built from the status, then the chart. Missing days are drawn as a gap, not a zero. | P1, P2, P3 |
| Setup | Five steps on main, "Step n of 5" | Five segments that fill as each stage completes, with the elapsed clock kept. Same five stages as main. v3's four-stage change is not used. | P2 |
| Setup done | Primary "Done" | Primary "Go to my plants" with a short success block (plant name, setup time). | P3, P1 |
| Empty state | Primary "Add your first plant" | Same button. Sensor explainer stays one tap away. | P5 |

## 2. Screen rules

**My plants**
- The top card shows only counts above zero, in words: "2 plants need water". One filled action. No counts, no card.
- Each row: name, room, status chip, a 0 to 100 % meter with dry and wet limits marked as ticks. The meter is decorative for assistive tech; the row's accessible label stays unchanged.
- Pull to refresh is not added here (not verified in v3). The Refresh button stays.

**Plant detail**
- Hero: soil moisture at the display size (`type.number`), with the status chip under it.
- One next-step line from a fixed rule, not from AI. Examples of the rule (copy to be written in `strings/en.json`): below the dry limit, "Soil is below the dry limit. Water it." Above the wet limit, "Soil is wetter than the limit. Hold off watering." Otherwise, "Soil is in the healthy range."
- Chart: a day with no reading is a gap in the line with the label "No reading", never a zero. This is the second social angle in Poppy's note, so it must be shown in the app before any claim is made.
- "Photos" is the filled action. "Remove plant" stays a text-style danger action.

**Profile**
- The plan price is shown on Profile before Premium is tapped, using the price the store returns. If no price is available, show "Price available at checkout" rather than leaving the row empty.

**Setup**
- Five segments, one per stage: 1 find sensor, 2 connect code, 3 Wi-Fi, 4 name and link, 5 photo and plant details. Segments fill as stages finish.
- The elapsed clock stays on the right (NFR-03 needs it).
- No QR scan in this round (needs a dependency and a requirement check, review item S3).

## 3. Bench and test impact (per Lena's rule 1)

| Change | Bench step | Labels touched | Tests |
|---|---|---|---|
| "Needs water" card | Step 3 (`plants.row.a11y`, `plants.refresh`) | None. The card is not a row and does not match the row pattern. | `v3Structure.test.tsx` counts still hold |
| Meter on each row | Step 3 | None. Accessible label unchanged. | `plants.test.tsx` finds rows by name |
| Next-step line | None (plant detail not in bench) | New keys only (`plant.next.*`) | `strings.test.ts` needs the new keys |
| Gap in chart | None | `plant.chart.noReading` (new key) | New unit test for the gap case |
| Five segments | Step 2 does not read `a11y.setupProgress` | Progress label text | `setupFlow.test.tsx` "Step n of 5" lines |
| "Go to my plants" | Step 2 taps `setup.done.*` | Value of `setup.done.seePlant` changes; bench reads it at run time | Keep "All set!" and the time text |

**Bench rule:** any label or key change needs Peter's bench check and Ines's review first (playbook rule 2). None of this has been run on a device.

## 4. Social angles (Poppy's inspiration note, not new posts)

Two public Google Play listings were read for principles only. Their store text was readable this time, unlike the 26 Nov note. Nothing is copied: no layout, copy, icons, images or names are reused. The useful signal is in the user reviews, which were paraphrased below:

- **Reviews of the first listing** mention a missing price at checkout and an unavailable subscription. Lesson for us: show the price and the plan before the user asks. Our Profile page already says where it is; keep it visible.
- **Reviews of the second listing** mention the app crashing on basic actions and a sync that appears to have overwritten a year of history on a new phone. Lesson for us: data safety. This supports angle 3 in Poppy's note ("your data leaves with you"), which is still unverified until the export and delete gate are run on a phone.

Angles that may go to a post only after their backing output exists (unchanged from the 26 Nov note):
1. "A sensor that tells you before the plant wilts." Needs a bench run with a threshold alert before the lowest reading. Not allowed today.
2. "A missing day is a gap, not a zero." Needs the phone screenshot and the gap test output. This design makes the gap visible, which is what the screenshot would show.
3. "Your data leaves with you." Needs the export and delete test output on a phone.

No post drafts are added here. Owner approval goes through a Needs Arsany row.

## 5. Decisions

1. **Setup steps:** five, matching main (decided by Arsany, 26 Nov). Done.
2. **Tab bar:** three tabs (Plants, Alerts with badge, Profile), decided by Arsany, 26 Nov. Bench tab steps need Peter's check.
3. **Price visibility:** show the plan price on Profile before Premium is tapped (decided by Arsany, yes). Rule in section 2.
4. **Lena's role:** approved by Arsany (26 Nov). The role file status is updated in this PR.

## 6. What is not in this PR

- No change to `src/`, `strings/en.json`, `tokens.json` or `theme.ts`. Code follows only after the decisions above.
- No device screenshots. The mockup uses mock data and shows layout only.
- No bench run and no test run for this design.

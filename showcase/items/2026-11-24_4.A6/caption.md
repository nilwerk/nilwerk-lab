# Premium dashboard: 30- and 90-day history for paying accounts (no real render captured)

**What it shows.** The premium dashboard screen for each plant and window: a soil moisture range bar (lowest to highest reading, with the mean marked), and a bar graph comparing the first week with the last week. Free accounts see an upgrade message and make no request for plant history. Missing data (a plant with no soil readings, or a week with no readings) shows a plain notice and no graph.

**Status.** The screen, the graphs and the gap handling are merged. The analytics endpoint behind the screen is not deployed yet, so with real data the premium view is not yet visible end to end.

**Images.** None. No real render was captured, so this item has no picture. A picture from a phone or simulator would be added only after a real render exists.

**Verified on a PC.** The Jest suite with a mocked backend passes, covering the premium, free, loading, empty, error and gap states, and the typecheck is clean.

**Unverified.** Not run on a phone, not at phone width, not against a live backend.

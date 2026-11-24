# Connect your AI: create and revoke a personal key for your own AI assistant (no real render captured)

**What it shows.** A premium account can create a personal key in the app. The full key is shown once with a copy button and a warning, then only its first characters remain in the list. The key can be revoked after a confirmation step. The screen also gives copy-paste setup text for Claude (command line) and for any other MCP client, with placeholders for the server address and the key. Free accounts see a locked message and the app makes no key request for them.

**Status.** The screen, the key client and the profile entry are built against the documented key contract. The key service on the server side is not built yet, so with real data the flow is not visible end to end.

**Images.** None. No real render was captured, so this item has no picture. A picture from a phone or simulator would be added only after a real render exists.

**Verified on a PC.** The Jest suite with a mocked backend passes, covering premium generate, shown once, copy, revoke, free locked, error and loading states, and the typecheck is clean.

**Unverified.** Not run on a phone, not at phone width, not against a live backend. The copy action uses the browser clipboard on web and the system share sheet on a phone; neither was tried on a device.

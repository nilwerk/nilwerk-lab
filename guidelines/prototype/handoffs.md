# Handoffs between embedded, PCB and enclosure work

Adapted from Arsany's embedded-prototype, pcb-design and 3d-printing agent definitions (`skills/vendor/agents-reference/`). Each discipline owns its deliverable. When work crosses a boundary, the sender writes a self-contained brief; nobody guesses the other side's numbers.

## Embedded / firmware (Mira) → PCB (Emil)
Send, when known: required behaviour and interfaces (sensors, radio, debug, expansion); candidate modules with exact SKU and revision, marked "candidate" or "frozen"; power source, exact battery and charger identity, current limits, charge-while-running need; mechanical envelope and keep-outs; cost, volume, supplier and assembly constraints with the URLs and datasheets already gathered; open decisions and measured loads; the requested deliverable.

## PCB (Emil) → Enclosure (Yara)
Send: exact board outline and mounting holes (DXF or STEP), connector positions and heights with a datasheet source for each, component keep-outs and heights, antenna keep-out, battery and cable bend allowance. Anything not read from a datasheet is labelled ASSUMED.

## Embedded → Enclosure (Yara)
Send: the board and revision with the authoritative STEP or dimensioned drawing; required openings (USB, light window, vents, reset, battery lead exit, sensor apertures); intended use and orientation; assembly and service needs; printer, material and nozzle; prior fit results and items that need a measurement.

## Rules
- The sender states what is verified and what is assumed. The receiver does not upgrade an assumption to a fact.
- Do not substitute an unverified dev kit or part silently; ask before a substitution that changes behaviour or footprint.
- A research handoff does not authorise a purchase, a paid quote or sending files to a fabricator (TEAM §5).
- Each side links the other's deliverable from its README.

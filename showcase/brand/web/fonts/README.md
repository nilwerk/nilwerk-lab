# Self-hosted fonts for the web component kit

Files: Space Grotesk 700, Inter 400 and 600, JetBrains Mono 400 and 600 (latin subset, woff2). Licence: SIL Open Font License 1.1 (`LICENSE-*.txt` in this folder), which allows self-hosting and commercial use.

**Provenance (checked honestly):** the woff2 files are unmodified copies of the files in the npm package `@fontsource/*` version 5.3.0 (`files/<family>-latin-<weight>-normal.woff2`); I verified with a byte-for-byte compare against the installed package files, not by recompressing or subsetting them myself. Fontsource builds these files from the Google Fonts releases; I did **not** independently verify them against the upstream Google Fonts or the foundry repositories. Space Grotesk 500 is not shipped here because the kit does not use it (brand-kit allows it for headlines).

To refresh: `npm i @fontsource/space-grotesk @fontsource/inter @fontsource/jetbrains-mono` and copy the same file names.

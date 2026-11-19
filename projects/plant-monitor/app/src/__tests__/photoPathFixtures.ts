// Shared good/bad photo path list for the rule '<uid>/<plant_id>/<uuid>.<ext>' (3 segments, [A-Za-z0-9._-], first = owner).
// The same cases belong in the cloud export tests (cloud/test/functions/export.test.ts, table BAD_PATHS) so both runtimes keep one rule; keep the lists in step.
export const UID = '11111111-1111-4111-8111-111111111111';
export const PL = '22222222-2222-4222-8222-222222222222';
const FL = '33333333-3333-4333-8333-333333333333';

export const GOOD_PATHS: [string, string][] = [
  ['plain jpg', `${UID}/${PL}/${FL}.jpg`],
  ['dots, dash, underscore inside a name', `${UID}/${PL}/a.b-c_d.jpg`],
  ['other app extensions', `${UID}/${PL}/${FL}.heic`],
];

export const BAD_PATHS: [string, string][] = [
  ['two segments', `${UID}/${FL}.jpg`],
  ['four segments', `${UID}/${PL}/x/${FL}.jpg`],
  ['leading slash', `/${UID}/${PL}/${FL}.jpg`],
  ['dot-dot as a segment', `${UID}/${PL}/..`],
  ['dot-dot inside a name', `${UID}/${PL}/a..jpg`],
  ['dot segment', `${UID}/./${FL}.jpg`],
  ['backslashes', `${UID}\\${PL}\\${FL}.jpg`],
  ['percent-encoded dot', `${UID}/${PL}/%2e%2e`],
  ['empty last segment', `${UID}/${PL}/`],
  ['empty middle segment', `${UID}//${FL}.jpg`],
  ['space in name', `${UID}/${PL}/a b.jpg`],
  ['control character', `${UID}/${PL}/a\u0000.jpg`],
  ['foreign owner', `11111111-1111-4111-8111-111111111112/${PL}/${FL}.jpg`],
  ['owner prefix only (uid + x)', `${UID}x/${PL}/${FL}.jpg`],
  ['not a string', null as unknown as string],
];

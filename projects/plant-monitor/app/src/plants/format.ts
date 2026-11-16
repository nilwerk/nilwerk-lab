// Date labels for the hourly table and the gallery. Plain code, no Intl, so Hermes and Jest print the same text.
const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
const two = (n: number) => String(n).padStart(2, '0');

/** "12 Nov 2026" in the phone's local time zone */
export function fmtDay(iso: string): string {
  const d = new Date(iso);
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

/** "11-09 12:00" in local time (table row label, start of the hour) */
export function fmtHour(iso: string): string {
  const d = new Date(iso);
  return `${two(d.getMonth() + 1)}-${two(d.getDate())} ${two(d.getHours())}:00`;
}

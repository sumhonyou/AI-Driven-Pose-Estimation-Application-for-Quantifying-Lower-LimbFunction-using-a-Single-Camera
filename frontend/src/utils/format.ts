// Shared text-formatting helpers.

/** Converts a snake_case enum/code value into a human-readable title, e.g. "sit_to_stand" -> "Sit To Stand". */
export function humanizeLabel(value: string | null | undefined): string {
  if (!value) return "";
  return value
    .split("_")
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/** Basic, permissive email format check for client-side validation (not a full RFC 5322 validator). */
export function isValidEmailFormat(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim());
}

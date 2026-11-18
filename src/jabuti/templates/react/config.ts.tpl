/**
 * Single source of the API base URL, read from VITE_API_BASE_URL at build
 * time. An empty value means "same origin". Never put secrets here: every
 * VITE_ variable ends up in the browser bundle.
 */
export const apiBaseUrl: string = normalizeBaseUrl(
  import.meta.env.VITE_API_BASE_URL ?? '',
);

export function normalizeBaseUrl(value: string): string {
  return value.trim().replace(/\/+$/, '');
}

/** Join the base URL and a path with exactly one slash between them. */
export function apiUrl(path: string, baseUrl: string = apiBaseUrl): string {
  return `${normalizeBaseUrl(baseUrl)}/${path.replace(/^\/+/, '')}`;
}

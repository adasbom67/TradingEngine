const configuredOrigin = (import.meta.env.VITE_API_ORIGIN as string | undefined)
  ?.trim()
  .replace(/\/+$/, "");

/**
 * Build an API URL for both supported application modes:
 *
 * - Vite development uses the `/api` proxy configured in `vite.config.ts`.
 * - The desktop build is served by the embedded FastAPI process and therefore
 *   uses the same origin as the UI.
 */
export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${configuredOrigin ?? ""}${normalizedPath}`;
}

/**
 * Unified PayScope API client configuration and resilient fetch utilities.
 * Handles Render cold starts, environment variable resolution, and network retries.
 */

export function getApiBaseUrl(): string {
  // 1. Explicit env variables (supports NEXT_PUBLIC_API_URL, NEXT_PUBLIC_API_BASE_URL, and API_BASE_URL)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL.replace(/\/+$/, "");
  }
  if (process.env.NEXT_PUBLIC_API_BASE_URL) {
    return process.env.NEXT_PUBLIC_API_BASE_URL.replace(/\/+$/, "");
  }
  if (process.env.API_BASE_URL) {
    return process.env.API_BASE_URL.replace(/\/+$/, "");
  }

  // 2. Production Vercel environment detection (both client-side and server-side)
  if (process.env.VERCEL || process.env.NEXT_PUBLIC_VERCEL_ENV || process.env.NODE_ENV === "production") {
    return "https://payscope-api.onrender.com";
  }

  // 3. Production browser runtime fallback (e.g. deployed on Vercel)
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (hostname !== "localhost" && hostname !== "127.0.0.1") {
      return "https://payscope-api.onrender.com";
    }
  }

  // 4. Local development fallback
  return "http://127.0.0.1:8000";
}

export interface FetchOptions extends RequestInit {
  timeoutMs?: number;
  retries?: number;
  retryDelayMs?: number;
  onRetry?: (attempt: number, error: unknown) => void;
}

/**
 * Fetch wrapper with timeout and progressive retry backoff for handling Render free-tier cold starts.
 */
export async function fetchWithRetry(
  endpoint: string,
  options: FetchOptions = {}
): Promise<Response> {
  const {
    timeoutMs = 15000,
    retries = 3,
    retryDelayMs = 2000,
    onRetry,
    ...fetchInit
  } = options;

  const base = getApiBaseUrl();
  const url = endpoint.startsWith("http") ? endpoint : `${base}${endpoint.startsWith("/") ? "" : "/"}${endpoint}`;

  let lastError: unknown = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(url, {
        ...fetchInit,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      // Retry on 502, 503, 504 (typical Render waking/gateway states)
      if ([502, 503, 504].includes(response.status) && attempt < retries) {
        if (onRetry) onRetry(attempt + 1, new Error(`Server returned status ${response.status}`));
        await new Promise((resolve) => setTimeout(resolve, retryDelayMs * Math.pow(1.5, attempt)));
        continue;
      }

      return response;
    } catch (err: unknown) {
      clearTimeout(timeoutId);
      lastError = err;

      if (attempt < retries) {
        if (onRetry) onRetry(attempt + 1, err);
        await new Promise((resolve) => setTimeout(resolve, retryDelayMs * Math.pow(1.5, attempt)));
      }
    }
  }

  throw lastError instanceof Error ? lastError : new Error("Failed to connect to PayScope API after retries.");
}

import { getCsrfToken } from "@/lib/utils/csrf";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api";
const CSRF_ENDPOINT = "/auth/csrf";
const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

let csrfCookieEnsured = false;
let csrfCookiePromise: Promise<void> | null = null;

export async function ensureCsrfCookie(): Promise<void> {
  if (csrfCookieEnsured) {
    return;
  }

  if (!csrfCookiePromise) {
    csrfCookiePromise = (async () => {
      const response = await fetch(`${API_BASE}${CSRF_ENDPOINT}`, {
        method: "GET",
        credentials: "include"
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Failed to initialize CSRF cookie");
      }
      csrfCookieEnsured = true;
    })().finally(() => {
      csrfCookiePromise = null;
    });
  }

  await csrfCookiePromise;
}

export async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${API_BASE}${normalizedPath}`;
  const headers = new Headers(options.headers ?? {});

  const method = options.method?.toUpperCase() ?? "GET";
  const isMutating = MUTATING_METHODS.has(method);

  if (isMutating) {
    if (normalizedPath !== CSRF_ENDPOINT) {
      await ensureCsrfCookie();
    }

    const csrf = getCsrfToken();
    if (csrf) {
      headers.set("X-CSRF-Token", csrf);
    }

    if (
      options.body &&
      !(options.body instanceof FormData) &&
      !headers.has("Content-Type")
    ) {
      headers.set("Content-Type", "application/json");
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "include"
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  if (!text) {
    return undefined as T;
  }

  return JSON.parse(text) as T;
}

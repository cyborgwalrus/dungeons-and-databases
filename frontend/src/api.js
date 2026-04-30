export const API_BASE = 'https://dnd-backend-6ymc.onrender.com/api';
const AUTH_TOKEN_KEY = 'dnd.auth.token';

/** Return the stored auth token, or null when none exists. */
export function getAuthToken() {
  try {
    return window.localStorage.getItem(AUTH_TOKEN_KEY);
  } catch (_err) {
    return null;
  }
}

/** Persist or clear the auth token in local storage. */
export function setAuthToken(token) {
  try {
    if (!token) {
      window.localStorage.removeItem(AUTH_TOKEN_KEY);
      return;
    }
    window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  } catch (_err) {
    /* ignore storage failures */
  }
}

/** Remove any cached auth token. */
export function clearAuthToken() {
  setAuthToken(null);
}

/** Fetch JSON from the API while attaching auth headers when available. */
export async function fetchJson(path, options) {
  try {
    const authToken = getAuthToken();
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      credentials: 'omit',
      headers: {
        'Content-Type': 'application/json',
        'ngrok-skip-browser-warning': 'true',
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...(options?.headers || {})
      }
    });
    const contentType = res.headers.get('content-type') || '';
    let data = null;
    if (contentType.includes('application/json')) {
      data = await res.json();
    } else {
      const text = await res.text();
      data = text
        ? { error: `${res.status} ${res.statusText}` }
        : { error: `${res.status} ${res.statusText}` };
    }
    return { ok: res.ok, status: res.status, data };
  } catch (e) {
    console.error('Fetch error', e);
    return { ok: false, status: 0, data: { error: 'Network error' } };
  }
}

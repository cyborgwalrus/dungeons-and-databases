export const API_BASE = window.__API_BASE__ || '/api';
const AUTH_TOKEN_KEY = 'dnd.auth.token';

export function getAuthToken() {
  try {
    return window.localStorage.getItem(AUTH_TOKEN_KEY);
  } catch (_err) {
    return null;
  }
}

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

export function clearAuthToken() {
  setAuthToken(null);
}

export async function fetchJson(path, options) {
  try {
    const authToken = getAuthToken();
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      credentials: 'omit',
      headers: {
        'Content-Type': 'application/json',
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...(options?.headers || {})
      }
    });
    const data = await res.json();
    return { ok: res.ok, status: res.status, data };
  } catch (e) {
    console.error('Fetch error', e);
    return { ok: false, status: 0, data: null };
  }
}

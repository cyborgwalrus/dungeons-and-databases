export const API_BASE = (window.__API_BASE__ || 'http://localhost:5000') + '/api';

export async function fetchJson(path, options) {
  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...options,
      credentials: 'include', // Include cookies for session management
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      }
    });
    const data = await res.json();
    return { ok: res.ok, data };
  } catch (e) {
    console.error('Fetch error', e);
    return { ok: false, data: null };
  }
}

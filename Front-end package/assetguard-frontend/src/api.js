// Centralized API client for AssetGuard backend.
// - Uses JWT access token from localStorage
// - Auto-refreshes via /api/token/refresh/ on 401 then retries the request once
// - Throws an Error with `.status` and `.data` so callers can show backend messages

export const API_BASE = 'http://127.0.0.1:8000';

const ACCESS_KEY = 'access_token';
const REFRESH_KEY = 'refresh_token';

export const tokens = {
  getAccess: () => localStorage.getItem(ACCESS_KEY),
  getRefresh: () => localStorage.getItem(REFRESH_KEY),
  set: (access, refresh) => {
    if (access) localStorage.setItem(ACCESS_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

async function refreshAccessToken() {
  const refresh = tokens.getRefresh();
  if (!refresh) return null;
  const r = await fetch(`${API_BASE}/api/token/refresh/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh }),
  });
  if (!r.ok) return null;
  const data = await r.json();
  if (data.access) {
    tokens.set(data.access, null);
    return data.access;
  }
  return null;
}

// Subscribers notified when refresh fails (so the app can redirect to /login).
const authFailureListeners = new Set();
export function onAuthFailure(fn) {
  authFailureListeners.add(fn);
  return () => authFailureListeners.delete(fn);
}
function fireAuthFailure() {
  tokens.clear();
  authFailureListeners.forEach((fn) => {
    try { fn(); } catch (_) { /* ignore */ }
  });
}

/**
 * Low-level request. `body` may be a plain object (auto JSON) or FormData.
 * Set `auth: false` for unauthenticated calls (e.g. login).
 */
export async function request(path, { method = 'GET', body, auth = true, headers = {} } = {}) {
  const url = path.startsWith('http') ? path : `${API_BASE}${path}`;
  const isForm = typeof FormData !== 'undefined' && body instanceof FormData;

  const buildHeaders = () => {
    const h = { ...headers };
    if (body !== undefined && !isForm) h['Content-Type'] = 'application/json';
    if (auth) {
      const t = tokens.getAccess();
      if (t) h['Authorization'] = `Bearer ${t}`;
    }
    return h;
  };

  const doFetch = () => fetch(url, {
    method,
    headers: buildHeaders(),
    body: body === undefined ? undefined : (isForm ? body : JSON.stringify(body)),
  });

  let response = await doFetch();

  // Try one transparent refresh on 401 for authenticated calls.
  if (response.status === 401 && auth) {
    const newAccess = await refreshAccessToken();
    if (newAccess) {
      response = await doFetch();
    } else {
      fireAuthFailure();
    }
  }

  // Parse body (json if possible, else text).
  const text = await response.text();
  let data = null;
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }

  if (!response.ok) {
    const err = new Error(
      (data && (data.detail || (typeof data === 'object' && Object.values(data).flat().join(' '))))
      || `Request failed (${response.status})`
    );
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data;
}

// ─── High-level API helpers (mirror docs/api.md) ────────────────────────────

export const api = {
  // Auth
  login: (username, password) =>
    request('/api/token/', { method: 'POST', body: { username, password }, auth: false })
      .then((d) => { tokens.set(d.access, d.refresh); return d; }),
  logout: () => { tokens.clear(); },

  // Assets
  listAssets: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/api/assets/${qs ? `?${qs}` : ''}`);
  },
  getAsset: (id) => request(`/api/assets/${id}/`),

  // Locations
  listLocations: () => request('/api/locations/'),
  getLocation: (id) => request(`/api/locations/${id}/`),

  // Load capacities
  listLoadCapacities: () => request('/api/load-capacities/'),

  // Equipment options
  listEquipmentOptions: () => request('/api/equipment-options/'),

  // Assessments
  listAssessments: () => request('/api/assessments/'),
  createAssessment: (payload) =>
    request('/api/assessments/', { method: 'POST', body: payload }),

  // PDF extract (admin)
  extractPdf: (file, autoSave = false) => {
    const fd = new FormData();
    fd.append('file', file);
    if (autoSave) fd.append('auto_save', 'true');
    return request('/api/extract/', { method: 'POST', body: fd });
  },
};

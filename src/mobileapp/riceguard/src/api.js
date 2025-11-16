import { API_BASE_URL, API_ORIGIN } from './config';

const DEFAULT_TIMEOUT_MS = 10_000;
const jsonHeaders = { 'Content-Type': 'application/json', Accept: 'application/json' };

async function parseJsonResponse(response) {
  const text = await response.text();
  if (!text) return {};
  try {
    return JSON.parse(text);
  } catch (err) {
    throw new Error(`Failed to parse JSON response: ${err?.message || err}`);
  }
}

async function handleResponse(response) {
  if (response.ok) {
    return parseJsonResponse(response);
  }

  let errorMessage = `Request failed with status ${response.status}`;
  try {
    const body = await parseJsonResponse(response);
    if (body?.detail) {
      errorMessage = Array.isArray(body.detail)
        ? body.detail.map((d) => (typeof d === 'string' ? d : d?.msg)).join(', ')
        : body.detail;
    } else if (body?.message) {
      errorMessage = body.message;
    }
  } catch (_) {
    // ignore parse errors; fall back to status
  }
  throw new Error(errorMessage);
}

async function request(url, options = {}, timeoutMs = DEFAULT_TIMEOUT_MS) {
  const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timer = controller ? setTimeout(() => controller.abort(), timeoutMs) : null;

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller ? controller.signal : undefined,
    });
    return await handleResponse(response);
  } catch (err) {
    if (controller && err?.name === 'AbortError') {
      throw new Error('Request timed out. Check your network connection.');
    }
    if (err?.message?.includes('Network request failed')) {
      throw new Error('Cannot reach the backend server. Verify API_BASE_URL and network connectivity.');
    }
    throw err;
  } finally {
    if (timer) clearTimeout(timer);
  }
}

export async function registerUser({ name, email, password }) {
  const effectiveName = name || email.split('@')[0] || 'RiceGuard User';
  return request(`${API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify({ name: effectiveName, email, password }),
  });
}

export async function loginUser({ email, password }) {
  return request(`${API_BASE_URL}/auth/login`, {
    method: 'POST',
    headers: jsonHeaders,
    body: JSON.stringify({ email, password }),
  });
}

export async function createScan({ uri, token, notes, modelVersion = '1.0' }) {
  if (!token) throw new Error('Missing auth token');

  const fileName = uri.split('/').pop() || 'photo.jpg';
  const match = /\.([^.]+)$/.exec(fileName);
  const extension = match ? match[1].toLowerCase() : 'jpg';
  const type = extension === 'png' ? 'image/png' : 'image/jpeg';

  const data = new FormData();
  data.append('file', { uri, name: fileName, type });
  if (notes) data.append('notes', notes);
  if (modelVersion) data.append('modelVersion', modelVersion);

  return request(`${API_BASE_URL}/scans`, {
    method: 'POST',
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: data,
  });
}

export async function listScans(token) {
  if (!token) throw new Error('Missing auth token');
  const json = await request(`${API_BASE_URL}/scans`, {
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${token}`,
    },
  });
  return json?.items ?? [];
}

export async function deleteScans(token, ids) {
  if (!token) throw new Error('Missing auth token');
  if (!Array.isArray(ids) || ids.length === 0) return { deletedCount: 0 };

  return request(`${API_BASE_URL}/scans/bulk-delete`, {
    method: 'POST',
    headers: {
      ...jsonHeaders,
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ ids }),
  });
}

export async function fetchRecommendation(diseaseKey) {
  if (!diseaseKey || diseaseKey === 'uncertain') return null;
  try {
    return await request(`${API_BASE_URL}/recommendations/${encodeURIComponent(diseaseKey)}`, {
      headers: { Accept: 'application/json' },
    });
  } catch (err) {
    console.warn(`Failed to load recommendation for ${diseaseKey}: ${err?.message || err}`);
    return null;
  }
}

export function resolveImageUrl(path) {
  if (!path) return null;
  if (/^https?:\/\//i.test(path)) return path;
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${API_ORIGIN}${normalized}`;
}

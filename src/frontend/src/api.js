// src/api.js

import { tokenStorage } from './secureStorage.js';
import { safeFetch } from './errorHandler.js';

const BASE_URL =
  import.meta?.env?.VITE_API_URL ||
  process.env.REACT_APP_API_URL ||
  "http://127.0.0.1:8000/api/v1";

// Derive backend origin (e.g., http://127.0.0.1:8000) from BASE_URL
export const BACKEND_BASE = BASE_URL.replace(/\/?api\/?v\d+.*/i, "").replace(/\/$/, "");

function jsonHeaders() {
  return { "Content-Type": "application/json" };
}

// Enhanced auth header that gets token securely
function secureAuthHeader() {
  const token = tokenStorage.getValidatedToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function register({ name, email, password }) {
  const res = await safeFetch(`${BASE_URL}/auth/register`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ name, email, password }),
  });
  return res.json(); // { id, name, email }
}

export async function login({ email, password }) {
  const res = await safeFetch(`${BASE_URL}/auth/login`, {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify({ email, password }),
    credentials: 'include', // Important for cookies
  });
  const data = await res.json(); // { accessToken, user:{id,name,email} }

  // Store token securely for backward compatibility
  if (data.accessToken && data.user) {
    tokenStorage.setToken(data.accessToken, data.user);
  }

  return data;
}

export async function logout() {
  try {
    const res = await safeFetch(`${BASE_URL}/auth/logout`, {
      method: "POST",
      credentials: 'include',
    });
    return res.json();
  } catch (error) {
    // Even if logout request fails, clear local storage
    console.warn('Logout request failed:', error.message);
  } finally {
    // Always clear local storage
    tokenStorage.clearToken();
  }
}

export async function uploadScan({ file, notes = null, modelVersion = "1.0" }) {
  const form = new FormData();
  form.append("file", file);
  if (notes != null) form.append("notes", notes);
  form.append("modelVersion", modelVersion);

  const res = await safeFetch(`${BASE_URL}/scans`, {
    method: "POST",
    headers: secureAuthHeader(),
    credentials: 'include',
    body: form,
  });
  return res.json(); // ScanItem
}

export async function listScans(page = 1, pageSize = 20, sortBy = "createdAt", sortOrder = "desc") {
  const params = new URLSearchParams({
    page: page.toString(),
    pageSize: pageSize.toString(),
    sortBy,
    sortOrder,
  });

  const res = await safeFetch(`${BASE_URL}/scans?${params}`, {
    headers: secureAuthHeader(),
    credentials: 'include',
  });
  return res.json(); // { items: ScanItem[], total, page, pageSize, hasNext, hasPrev }
}

// ✅ Original delete endpoints (kept for compatibility)
export async function deleteScan(id) {
  const res = await safeFetch(`${BASE_URL}/scans/${id}`, {
    method: "DELETE",
    headers: secureAuthHeader(),
    credentials: 'include',
  });
  return res.json(); // { deleted: true, id }
}

export async function bulkDeleteScans(ids) {
  const res = await safeFetch(`${BASE_URL}/scans/bulk-delete`, {
    method: "POST",
    headers: { ...secureAuthHeader(), ...jsonHeaders() },
    credentials: 'include',
    body: JSON.stringify({ ids }),
  });
  return res.json(); // { deletedCount: number }
}

export async function getRecommendation(diseaseKey) {
  const res = await safeFetch(`${BASE_URL}/recommendations/${encodeURIComponent(diseaseKey)}`);
  return res.json(); // { diseaseKey, title, steps, version, updatedAt }
}

// ✅ Fixed buildImageUrl with support for full absolute URLs
export function buildImageUrl(relPath) {
  if (!relPath) return null;
  if (/^https?:\/\//i.test(relPath)) return relPath; // already absolute
  const clean = String(relPath).replace(/^\/+/, "");
  return `${BACKEND_BASE}/${clean}`;
}

// ✅ Added simplified variant (alias for backward compatibility)
export async function bulkDelete(ids) {
  const res = await safeFetch(`${BASE_URL}/scans/bulk-delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...secureAuthHeader() },
    credentials: 'include',
    body: JSON.stringify({ ids }),
  });
  return res.json(); // { deletedCount }
}

// ✅ User Profile API endpoints
export async function getUserProfile() {
  const res = await safeFetch(`${BASE_URL}/user/profile`, {
    method: "GET",
    headers: secureAuthHeader(),
    credentials: 'include',
  });
  return res.json(); // { id, name, email, bio, avatar, createdAt, updatedAt }
}

export async function updateUserProfile(profileData) {
  const res = await safeFetch(`${BASE_URL}/user/profile`, {
    method: "PUT",
    headers: secureAuthHeader(),
    credentials: 'include',
    body: profileData, // FormData for file upload
  });
  return res.json(); // { id, name, email, bio, avatar, updatedAt }
}

export async function updateAvatar(avatarFile) {
  const formData = new FormData();
  formData.append('avatar', avatarFile);

  const res = await safeFetch(`${BASE_URL}/user/avatar`, {
    method: "PUT",
    headers: secureAuthHeader(),
    credentials: 'include',
    body: formData,
  });
  return res.json(); // { avatar: string }
}

// src/services/api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://codea-orchestrator.azurewebsites.net';
const API_URL = `${API_BASE_URL}/api`;
const FUNCTION_KEY = 'APgUNXw0hbrLWtTjXHnXUU6JwAXKjZbeMMa9enOmNYW9AzFup1vvTA==';

// ============ CHAT ============
export async function sendQuestion(question) {
  const url = `${API_URL}/ask?code=${FUNCTION_KEY}`;
  console.log(`[API] Enviando pregunta a: ${url}`);
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ question }),
    });
    if (!response.ok) {
      const errorText = await response.text();
      console.error(`[API] Error HTTP ${response.status}: ${errorText}`);
      throw new Error(`Error al consultar el asistente (${response.status})`);
    }
    const data = await response.json();
    console.log('[API] Respuesta recibida:', data);
    return data.answer;
  } catch (error) {
    console.error('[API] Excepción en sendQuestion:', error);
    throw error;
  }
}

// ============ ADMINISTRACIÓN ============
function getAuthToken() {
  return localStorage.getItem('admin_token');
}

export function isAuthenticated() {
  const token = getAuthToken();
  const expiry = localStorage.getItem('admin_token_expiry');
  if (!token || !expiry) return false;
  return Date.now() < parseInt(expiry, 10);
}

export async function login(username, password) {
  const response = await fetch(`${API_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data || 'Credenciales inválidas');
  }
  return data; // { token, expires_in }
}

export function logout() {
  localStorage.removeItem('admin_token');
  localStorage.removeItem('admin_token_expiry');
}

export async function getDocuments(search = '', limit = 50, offset = 0) {
  const token = getAuthToken();
  const url = `${API_URL}/documents?search=${encodeURIComponent(search)}&limit=${limit}&offset=${offset}`;
  const response = await fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Error al obtener documentos');
  }
  return response.json();
}

export async function deleteDocument(docId) {
  const token = getAuthToken();
  const response = await fetch(`${API_URL}/documents/delete?id=${docId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Error al eliminar documento');
  }
  return response.json();
}

export async function getDownloadUrl(docId) {
  const token = getAuthToken();
  const response = await fetch(`${API_URL}/documents/download?id=${docId}`, {
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error || 'Error al obtener URL de descarga');
  }
  return response.json(); // { download_url }
}

// ============ SUBIDA DE ARCHIVOS (MODIFICADA) ============
export async function uploadFile(file, hash, title = '', normCode = '') {
  const token = getAuthToken();
  const formData = new FormData();
  formData.append('file', file);
  formData.append('hash', hash);
  formData.append('title', title);
  formData.append('normCode', normCode);
  
  const response = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    body: formData,
    headers: { 'Authorization': `Bearer ${token}` },
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.error || 'Error al subir archivo');
  }
  return data;
}

// ============ UTILIDADES ============
export async function computeFileHash(file) {
  const buffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
}
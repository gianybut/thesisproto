// Token handling is kept behind this module so the rest of the app never knows
// what the bearer value is: a signed, expiring JWT from /api/auth/login
// (backend/auth_tokens.py). Expiry shows up as a 401 on any call, which
// handleUnauthorized() turns into a return to the login screen.
import * as SecureStore from 'expo-secure-store';
import { DEFAULT_SERVER_URL } from './config';

const K_TOKEN = 'bk_token';
const K_USER = 'bk_user';
const K_SERVER = 'bk_server_url';

let token = null;
let user = null;
let serverUrl = DEFAULT_SERVER_URL;
const unauthorizedListeners = new Set();

export async function loadAuth() {
  token = await SecureStore.getItemAsync(K_TOKEN);
  const u = await SecureStore.getItemAsync(K_USER);
  user = u ? JSON.parse(u) : null;
  serverUrl = (await SecureStore.getItemAsync(K_SERVER)) || DEFAULT_SERVER_URL;
  return { token, user, serverUrl };
}

export const getToken = () => token;
export const getUser = () => user;
export const getServerUrl = () => serverUrl;
export const authHeader = () => (token ? { Authorization: `Bearer ${token}` } : {});

export function tokenFromLogin(body) {
  if (!body.token) throw new Error('The server did not return a login token. Update the backend.');
  return body.token;
}

export async function setServerUrl(url) {
  serverUrl = url.trim().replace(/\/+$/, '');
  await SecureStore.setItemAsync(K_SERVER, serverUrl);
}

export async function login(username, password) {
  let res;
  try {
    res = await fetch(`${serverUrl}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
  } catch {
    throw new Error(`Could not reach ${serverUrl}. Check the server address and that the phone is on the same network.`);
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || `Login failed (HTTP ${res.status})`);

  token = tokenFromLogin(body);
  user = body.user;
  await SecureStore.setItemAsync(K_TOKEN, token);
  await SecureStore.setItemAsync(K_USER, JSON.stringify(user));
  return user;
}

export async function logout() {
  token = null;
  user = null;
  await SecureStore.deleteItemAsync(K_TOKEN);
  await SecureStore.deleteItemAsync(K_USER);
}

/**
 * Check the stored token against the server. Returns false only when the server
 * definitely refused it; being offline in the field is not a reason to log out.
 */
export async function verifyToken() {
  if (!token) return false;
  try {
    const res = await fetch(`${serverUrl}/api/auth/me`, { headers: authHeader() });
    if (res.status === 401) return false;
  } catch {
    // offline: keep the session
  }
  return true;
}

export function onUnauthorized(fn) {
  unauthorizedListeners.add(fn);
  return () => unauthorizedListeners.delete(fn);
}

/** Any API call that gets a 401 calls this; the app returns to the login screen. */
export async function handleUnauthorized() {
  await logout();
  unauthorizedListeners.forEach((fn) => fn());
}

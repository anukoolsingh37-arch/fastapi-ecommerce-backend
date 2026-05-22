const AUTH_TOKEN_KEY = 'shop_ease_token';
const AUTH_USER_KEY = 'shop_ease_user';

const state = {
  token: localStorage.getItem(AUTH_TOKEN_KEY) || null,
  user: JSON.parse(localStorage.getItem(AUTH_USER_KEY) || 'null')
};

function saveAuth(token, user) {
  state.token = token;
  state.user = user;
  localStorage.setItem(AUTH_TOKEN_KEY, token);
  localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
}

function clearAuth() {
  state.token = null;
  state.user = null;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}

function getAuthHeaders() {
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  return headers;
}

async function apiFetch(path, options = {}) {
  const fetchOptions = { headers: getAuthHeaders(), ...options };
  if (options.body && !(options.body instanceof FormData)) {
    fetchOptions.body = JSON.stringify(options.body);
  }
  const response = await fetch(path, fetchOptions);
  let body;
  try {
    body = await response.json();
  } catch (error) {
    body = { detail: 'Invalid response from server' };
  }
  if (!response.ok) {
    throw body;
  }
  return body;
}

async function loginUser(username, password) {
  const body = new URLSearchParams();
  body.append('username', username);
  body.append('password', password);

  const response = await fetch('/login', {
    method: 'POST',
    body,
  });

  if (!response.ok) {
    const error = await response.json();
    throw error;
  }

  const result = await response.json();
  saveAuth(result.access_token, result.user);
  return result;
}

async function registerUser(username, email, password) {
  const result = await apiFetch('/users/', {
    method: 'POST',
    body: { username, email, password }
  });
  return result;
}

function formatPrice(value) {
  return `$${Number(value).toFixed(2)}`;
}

function getQueryParameter(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function updateAuthBanner(message) {
  const authMessage = document.getElementById('auth-message');
  if (authMessage) {
    authMessage.textContent = message;
  }
}

function ensureAuthMessage() {
  if (state.user) {
    updateAuthBanner(`Signed in as ${state.user.username}`);
  } else {
    updateAuthBanner('Login to access cart, wishlist, and orders.');
  }
}

function logoutUser() {
  clearAuth();
  ensureAuthMessage();
  window.location.reload();
}

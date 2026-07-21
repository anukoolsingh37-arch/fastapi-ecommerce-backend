// ===== Auth State =====
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
  refreshCartCount();
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

// ===== Toast Notification System =====
function ensureToastContainer() {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  return container;
}

function showToast(message, type = 'info', duration = 4000) {
  const container = ensureToastContainer();
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  toast.addEventListener('click', () => {
    toast.classList.add('toast-removing');
    setTimeout(() => toast.remove(), 300);
  });
  container.appendChild(toast);
  setTimeout(() => {
    toast.classList.add('toast-removing');
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ===== Loading Spinner =====
function createSpinner(large = false) {
  const div = document.createElement('div');
  div.className = large ? 'spinner spinner-lg' : 'spinner';
  return div;
}

function showLoading(container, message = 'Loading...') {
  container.innerHTML = '';
  const overlay = document.createElement('div');
  overlay.className = 'loading-overlay';
  overlay.id = 'loading-indicator';
  overlay.appendChild(createSpinner(true));
  const text = document.createElement('span');
  text.textContent = message;
  overlay.appendChild(text);
  container.appendChild(overlay);
}

// ===== Mobile Menu Toggle =====
function initMobileMenu() {
  const toggle = document.getElementById('mobile-menu-toggle');
  const nav = document.querySelector('.nav-links');
  if (toggle && nav) {
    toggle.addEventListener('click', () => {
      nav.classList.toggle('open');
    });
    // Close menu when clicking a link
    nav.querySelectorAll('a, button').forEach(el => {
      el.addEventListener('click', () => {
        nav.classList.remove('open');
      });
    });
  }
}

// ===== Consolidated API Fetch =====
async function apiFetch(path, options = {}) {
  const fetchOptions = { headers: getAuthHeaders(), ...options };
  if (options.body && !(options.body instanceof FormData) && !(options.body instanceof URLSearchParams)) {
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
    const error = new Error(body.detail || 'API request failed');
    error.status = response.status;
    error.body = body;
    throw error;
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
    throw new Error(error.detail || 'Login failed');
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
  showToast('Logged out successfully', 'info');
  window.location.reload();
}

// ===== Auth Modal UI =====
function openAuthModal(mode = 'login') {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');
  const title = document.getElementById('auth-title');
  if (title) title.textContent = mode === 'login' ? 'Sign in' : 'Create account';
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');
  if (loginForm) loginForm.style.display = mode === 'login' ? 'block' : 'none';
  if (registerForm) registerForm.style.display = mode === 'register' ? 'block' : 'none';
}

function closeAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
}

async function handleLogin() {
  const username = document.getElementById('login-username')?.value;
  const password = document.getElementById('login-password')?.value;
  if (!username || !password) {
    showToast('Please enter username and password', 'warning');
    return;
  }
  try {
    await loginUser(username, password);
    ensureAuthMessage();
    closeAuthModal();
    showToast('Signed in successfully', 'success');
  } catch (err) {
    showToast(err.message || 'Login failed', 'error');
  }
}

async function handleRegister() {
  const username = document.getElementById('reg-username')?.value;
  const email = document.getElementById('reg-email')?.value;
  const password = document.getElementById('reg-password')?.value;
  if (!username || !email || !password) {
    showToast('Please fill in all fields', 'warning');
    return;
  }
  try {
    await registerUser(username, email, password);
    showToast('Registration successful — you may sign in now', 'success');
    openAuthModal('login');
  } catch (err) {
    showToast(err.body?.detail || err.message || 'Registration failed', 'error');
  }
}

// ===== App Cart Helpers =====
async function refreshCartCount() {
  if (!state.token) {
    updateCartCount(0);
    return;
  }

  try {
    const items = await apiFetch('/cart/');
    const count = items.reduce((s, item) => s + (item.quantity || 0), 0);
    updateCartCount(count);
  } catch (error) {
    updateCartCount(0);
  }
}

function updateCartCount(count = 0) {
  const el = document.getElementById('cart-count');
  if (el) el.textContent = String(count);
}

// ===== Shipment Tracking Modal =====
function openShipmentModal(orderId) {
  // Remove existing shipment modal if any
  const existing = document.getElementById('shipment-modal');
  if (existing) existing.remove();

  const overlay = document.createElement('div');
  overlay.className = 'modal';
  overlay.id = 'shipment-modal';
  overlay.innerHTML = `
    <div class="modal-backdrop"></div>
    <div class="modal-content" style="max-width:500px;">
      <button class="modal-close">×</button>
      <div style="padding:28px;">
        <h2 style="margin-bottom:8px;">Shipments for Order #${orderId}</h2>
        <p style="color:var(--muted);font-size:0.9rem;margin-bottom:20px;">Tracking timeline</p>
        <div id="shipment-timeline" class="shipment-timeline">
          <div class="loading-overlay">${createSpinner().outerHTML}<span>Loading shipments...</span></div>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const closeModal = () => overlay.remove();
  overlay.querySelector('.modal-close').addEventListener('click', closeModal);
  overlay.querySelector('.modal-backdrop').addEventListener('click', closeModal);

  // Fetch and render shipments
  (async () => {
    try {
      const shipments = await apiFetch(`/shipments/order/${orderId}`);
      const timeline = document.getElementById('shipment-timeline');
      if (!shipments.length) {
        timeline.innerHTML = '<div class="empty-state">No shipments tracked for this order yet.</div>';
        return;
      }
      timeline.innerHTML = '';
      const statusOrder = ['pending', 'processing', 'shipped', 'delivered'];
      // Sort by status order, then by date
      shipments.sort((a, b) => {
        const aIdx = statusOrder.indexOf(a.status);
        const bIdx = statusOrder.indexOf(b.status);
        if (aIdx !== bIdx) return aIdx - bIdx;
        return new Date(b.created_at || 0) - new Date(a.created_at || 0);
      });
      shipments.forEach(s => {
        const step = document.createElement('div');
        step.className = 'shipment-step';
        const dotClass = s.status === 'delivered' ? 'completed' : (s.status === 'shipped' || s.status === 'processing' ? 'active' : '');
        step.innerHTML = `
          <div class="shipment-dot ${dotClass}"></div>
          <div class="shipment-info">
            <strong>${s.status.charAt(0).toUpperCase() + s.status.slice(1)}</strong>
            ${s.location ? `<span>📍 ${s.location}</span>` : ''}
            ${s.created_at ? `<span>📅 ${new Date(s.created_at).toLocaleString()}</span>` : ''}
            ${s.notes ? `<span>📝 ${s.notes}</span>` : ''}
          </div>
        `;
        timeline.appendChild(step);
      });
    } catch (err) {
      const timeline = document.getElementById('shipment-timeline');
      if (timeline) timeline.innerHTML = '<div class="empty-state">Could not load shipment data.</div>';
      showToast('Could not load shipments', 'error');
    }
  })();
}

// ===== Product / Category Fetching =====
async function fetchProducts(page = 1, limit = 100) {
  try {
    const data = await apiFetch(`/products?page=${page}&limit=${limit}`);
    if (!data) return [];
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.products)) return data.products;
    return [];
  } catch (err) {
    console.warn('product fetch failed', err);
    return [];
  }
}

async function fetchCategories() {
  try {
    const cats = await apiFetch('/categories');
    if (Array.isArray(cats)) return cats;
    return [];
  } catch (err) {
    console.warn('category fetch failed', err);
    return [];
  }
}

// ===== Product Rendering =====
function renderProducts(products = [], categories = []) {
  const grid = document.getElementById('product-grid');
  if (!grid) return;
  grid.innerHTML = '';
  products.forEach(p => {
    const card = document.createElement('div');
    card.className = 'product-card';
    const title = p.title || p.name || 'Untitled';
    const price = p.price || 0;
    const img = p.image && p.image.trim()
      ? p.image
      : 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=900&q=80';
    const categoryName = (categories.find(c => c.id === p.category_id) || {}).name || '';
    card.innerHTML = `
      <div class="card-media"><img src="${img}" alt="${title}" loading="lazy"/></div>
      <div class="card-body">
        <div style="display:flex;justify-content:space-between;align-items:start;gap:12px;">
          <div>
            <h3>${title}</h3>
            <p class="product-desc">${(p.description || '').substring(0, 120)}</p>
            ${categoryName ? `<div class="tag">${categoryName}</div>` : ''}
          </div>
          <div class="card-meta">
            <div><strong>${formatPrice(price)}</strong></div>
          </div>
        </div>
        <div class="card-actions">
          <div style="display:flex;gap:12px;">
            <button class="btn btn-sm btn-primary add-to-cart" data-id="${p.id}" data-name="${title}" data-price="${price}">Add to cart</button>
            <button class="btn btn-sm btn-outline view-details" data-id="${p.id}" data-name="${title}" data-price="${price}" data-description="${(p.description || '').replace(/"/g, '"')}" data-image="${img}" data-stock="${p.stock || 0}">Details</button>
          </div>
        </div>
      </div>
    `;
    grid.appendChild(card);
  });
}

function buildCategoryPills(categories = []) {
  const target = document.getElementById('category-pills');
  if (!target) return;
  target.innerHTML = '';
  categories.forEach(c => {
    const btn = document.createElement('button');
    btn.className = 'pill';
    btn.textContent = c.name;
    btn.dataset.id = c.id;
    btn.addEventListener('click', () => { btn.classList.toggle('active'); });
    target.appendChild(btn);
  });
}

function showCartModal() {
  const overlay = document.createElement('div');
  overlay.className = 'modal';
  overlay.innerHTML = `
    <div class="modal-backdrop"></div>
    <div class="modal-content">
      <button class="modal-close">×</button>
      <div style="padding:28px;max-height:70vh;overflow:auto;">
        <h2>Your cart</h2>
        <div id="cart-lines"></div>
        <div style="margin-top:18px;display:flex;justify-content:flex-end;gap:12px;">
          <button id="open-orders-btn" class="btn btn-primary">View Orders</button>
          <button id="close-cart" class="btn btn-outline">Close</button>
        </div>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);
  const closeBtn = overlay.querySelector('.modal-close');
  const closeSimple = overlay.querySelector('#close-cart');
  const closeModal = () => overlay.remove();
  closeBtn.addEventListener('click', closeModal);
  closeSimple.addEventListener('click', closeModal);
  overlay.querySelector('.modal-backdrop').addEventListener('click', closeModal);

  const lines = overlay.querySelector('#cart-lines');
  const openOrdersBtn = overlay.querySelector('#open-orders-btn');
  openOrdersBtn.addEventListener('click', () => {
    window.location.href = '/orders';
  });

  if (!state.token) {
    lines.innerHTML = `<div class="empty-state">Login to view your cart.</div>`;
    return;
  }

  (async () => {
    try {
      const cartItems = await apiFetch('/cart/');
      if (!cartItems.length) {
        lines.innerHTML = `<div class="empty-state">Your cart is empty</div>`;
        return;
      }

      lines.innerHTML = '';
      cartItems.forEach(item => {
        const row = document.createElement('div');
        row.className = 'panel-card';
        row.innerHTML = `
          <div>
            <strong>${item.product_name}</strong>
            <div style="color:var(--muted)">${item.quantity} × ${formatPrice(item.price)}</div>
          </div>
          <div style="display:flex;gap:8px;align-items:center;">
            <button class="btn btn-sm btn-outline remove-item" data-cart-id="${item.id}">Remove</button>
          </div>
        `;
        row.querySelector('.remove-item').addEventListener('click', async () => {
          try {
            await apiFetch(`/cart/${item.id}`, { method: 'DELETE' });
            row.remove();
            refreshCartCount();
          } catch (err) {
            showToast(err.body?.detail || err.message || 'Unable to remove item', 'error');
          }
        });
        lines.appendChild(row);
      });
    } catch (error) {
      lines.innerHTML = `<div class="empty-state">Could not load cart.</div>`;
    }
  })();
}

// ===== DOM Ready Init =====
document.addEventListener('DOMContentLoaded', () => {
  refreshCartCount();
  ensureAuthMessage();
  initMobileMenu();

  // Auth modal bindings
  document.querySelectorAll('.modal-close').forEach(btn => btn.addEventListener('click', closeAuthModal));
  document.getElementById('show-register')?.addEventListener('click', (e) => { e.preventDefault(); openAuthModal('register'); });
  document.getElementById('show-login')?.addEventListener('click', (e) => { e.preventDefault(); openAuthModal('login'); });
  document.getElementById('login-submit')?.addEventListener('click', (e) => { e.preventDefault(); handleLogin(); });
  document.getElementById('register-submit')?.addEventListener('click', (e) => { e.preventDefault(); handleRegister(); });

  // Cart button
  document.getElementById('cart-button')?.addEventListener('click', showCartModal);
});
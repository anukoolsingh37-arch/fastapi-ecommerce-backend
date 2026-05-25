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

// Auth modal UI
function openAuthModal(mode = 'login') {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');
  document.getElementById('auth-title').textContent = mode === 'login' ? 'Sign in' : 'Create account';
  document.getElementById('login-form').style.display = mode === 'login' ? 'block' : 'none';
  document.getElementById('register-form').style.display = mode === 'register' ? 'block' : 'none';
}

function closeAuthModal() {
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
}

async function handleLogin() {
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;
  try {
    const res = await loginUser(username, password);
    ensureAuthMessage();
    closeAuthModal();
    alert('Signed in');
  } catch (err) {
    alert(err.detail || JSON.stringify(err));
  }
}

async function handleRegister() {
  const username = document.getElementById('reg-username').value;
  const email = document.getElementById('reg-email').value;
  const password = document.getElementById('reg-password').value;
  try {
    const res = await registerUser(username, email, password);
    alert('Registration successful — you may sign in now');
    openAuthModal('login');
  } catch (err) {
    alert(err.detail || JSON.stringify(err));
  }
}

// --- Client storefront helpers: products, search, filters, cart ---
state.cart = JSON.parse(localStorage.getItem('shop_ease_cart') || '[]');

function saveCart() {
  localStorage.setItem('shop_ease_cart', JSON.stringify(state.cart));
  updateCartCount();
}

function updateCartCount() {
  const el = document.getElementById('cart-count');
  if (el) el.textContent = state.cart.reduce((s, i) => s + (i.qty || 1), 0);
}

function addToCart(product) {
  const idx = state.cart.findIndex(p => p.id === product.id);
  if (idx >= 0) {
    state.cart[idx].qty = (state.cart[idx].qty || 1) + 1;
  } else {
    state.cart.push({ ...product, qty: 1 });
  }
  saveCart();
}

function removeFromCart(productId) {
  state.cart = state.cart.filter(p => p.id !== productId);
  saveCart();
}

function changeCartQty(productId, qty) {
  const idx = state.cart.findIndex(p => p.id === productId);
  if (idx >= 0) {
    state.cart[idx].qty = Math.max(0, qty);
    if (state.cart[idx].qty === 0) removeFromCart(productId);
    else saveCart();
  }
}

async function fetchProducts() {
  try {
    const data = await apiFetch('/products?page=1&limit=100');
    if (!data) return [];
    if (Array.isArray(data)) return data;
    if (Array.isArray(data.products)) return data.products.map(p => ({ ...p }));
    return [];
  } catch (err) {
    console.warn('product fetch failed, using fallback', err);
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

function renderProducts(products = [], categories = []) {
  const grid = document.getElementById('product-grid');
  if (!grid) return;
  grid.innerHTML = '';
  products.forEach(p => {
    const card = document.createElement('div');
    card.className = 'product-card';
    const title = p.title || p.name || 'Untitled';
    const price = p.price || p.unit_price || 0;
    const img = p.image || '/static/product-placeholder.png';
    const categoryName = (categories.find(c => c.id === p.category_id) || {}).name || '';
    card.innerHTML = `
      <div class="card-media"><img src="${img}" alt="${title}"/></div>
      <div class="card-body">
        <div style="display:flex;justify-content:space-between;align-items:start;gap:12px;">
          <div>
            <h3>${title}</h3>
            <p class="product-desc">${(p.description || '').substring(0,120)}</p>
            ${categoryName ? `<div class="tag">${categoryName}</div>` : ''}
          </div>
          <div class="card-meta">
            <div><strong>${formatPrice(price)}</strong></div>
          </div>
        </div>
        <div class="card-actions">
          <div style="display:flex;gap:12px;">
            <button class="btn btn-sm btn-primary add-to-cart">Add to cart</button>
            <button class="btn btn-sm btn-outline view-details">Details</button>
          </div>
        </div>
      </div>
    `;

    const addBtn = card.querySelector('.add-to-cart');
    addBtn.addEventListener('click', () => { addToCart(p); });

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

function applyClientFilters(allProducts) {
  const q = document.getElementById('site-search')?.value?.toLowerCase() || '';
  const min = Number(document.getElementById('min-price')?.value || 0);
  const maxVal = document.getElementById('max-price')?.value;
  const max = maxVal ? Number(maxVal) : Number.MAX_SAFE_INTEGER;
  const activeCats = Array.from(document.querySelectorAll('#category-pills .pill.active')).map(n => Number(n.dataset.id));
  const sort = document.getElementById('sort-select')?.value || 'default';

  let results = allProducts.filter(p => {
    const text = `${p.title || p.name} ${p.description || ''}`.toLowerCase();
    if (q && !text.includes(q)) return false;
    const price = Number(p.price || p.unit_price || 0);
    if (price < min || price > max) return false;
    if (activeCats.length && !activeCats.includes(p.category_id)) return false;
    return true;
  });

  if (sort === 'price_asc') results.sort((a,b) => (a.price||a.unit_price||0) - (b.price||b.unit_price||0));
  if (sort === 'price_desc') results.sort((a,b) => (b.price||b.unit_price||0) - (a.price||a.unit_price||0));
  if (sort === 'name_asc') results.sort((a,b) => (a.name||a.title||'').localeCompare(b.name||b.title||''));

  renderProducts(results);
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
          <button id="checkout-btn" class="btn btn-primary">Checkout (mock)</button>
          <button id="close-cart" class="btn btn-outline">Close</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);
  const closeBtn = overlay.querySelector('.modal-close');
  const closeSimple = overlay.querySelector('#close-cart');
  closeBtn.addEventListener('click', () => overlay.remove());
  closeSimple.addEventListener('click', () => overlay.remove());

  const lines = overlay.querySelector('#cart-lines');
  if (state.cart.length === 0) {
    lines.innerHTML = `<div class="empty-state">Your cart is empty</div>`;
  } else {
    lines.innerHTML = '';
    state.cart.forEach(item => {
      const row = document.createElement('div');
      row.className = 'panel-card';
      row.innerHTML = `
        <div>
          <strong>${item.name}</strong>
          <div style="color:var(--muted)">${formatPrice(item.price || item.unit_price || 0)}</div>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
          <input type="number" min="0" value="${item.qty}" style="width:72px;padding:8px;border-radius:8px;border:1px solid var(--border)" />
          <button class="btn btn-sm btn-outline remove">Remove</button>
        </div>
      `;
      const input = row.querySelector('input');
      input.addEventListener('change', (e) => changeCartQty(item.id, Number(e.target.value)));
      row.querySelector('.remove').addEventListener('click', () => { removeFromCart(item.id); row.remove(); });
      lines.appendChild(row);
    });
  }

  document.getElementById('checkout-btn')?.addEventListener('click', () => {
    alert('Checkout is mocked in this demo.');
  });
}

document.addEventListener('DOMContentLoaded', async () => {
  updateCartCount();
  ensureAuthMessage();

  const allProducts = await fetchProducts();
  const categories = await fetchCategories();
  renderProducts(allProducts, categories);
  buildCategoryPills(categories);

  document.getElementById('cart-button')?.addEventListener('click', showCartModal);
  document.getElementById('apply-filters')?.addEventListener('click', () => applyClientFilters(allProducts));
  document.getElementById('clear-filters')?.addEventListener('click', () => {
    document.getElementById('min-price').value = '';
    document.getElementById('max-price').value = '';
    document.querySelectorAll('#category-pills .pill.active').forEach(n => n.classList.remove('active'));
    document.getElementById('site-search').value = '';
    renderProducts(allProducts, categories);
  });
  document.getElementById('site-search')?.addEventListener('input', () => applyClientFilters(allProducts));
  document.getElementById('sort-select')?.addEventListener('change', () => applyClientFilters(allProducts));

  // auth modal bindings
  document.querySelectorAll('.modal-close').forEach(btn => btn.addEventListener('click', closeAuthModal));
  document.getElementById('show-register')?.addEventListener('click', (e) => { e.preventDefault(); openAuthModal('register'); });
  document.getElementById('show-login')?.addEventListener('click', (e) => { e.preventDefault(); openAuthModal('login'); });
  document.getElementById('login-submit')?.addEventListener('click', (e) => { e.preventDefault(); handleLogin(); });
  document.getElementById('register-submit')?.addEventListener('click', (e) => { e.preventDefault(); handleRegister(); });

  // optionally open auth modal when clicking brand
  document.querySelector('.brand')?.addEventListener('click', () => openAuthModal('login'));
});

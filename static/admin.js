const adminState = {
  products: [],
  orders: [],
  coupons: [],
  categories: [],
  summary: null
};

function formatCurrency(value) {
  return `$${Number(value).toFixed(2)}`;
}

function renderAdminUser() {
  const userLabel = document.getElementById('stat-user');
  const loginBtn = document.getElementById('open-login');
  const logoutBtn = document.getElementById('admin-logout');
  if (!userLabel) return;
  if (state.user) {
    userLabel.textContent = `${state.user.username} (${state.user.is_admin ? 'admin' : 'user'})`;
    if (loginBtn) loginBtn.style.display = 'none';
    if (logoutBtn) logoutBtn.style.display = 'inline-flex';
  } else {
    userLabel.textContent = 'Not signed in';
    if (loginBtn) loginBtn.style.display = 'inline-flex';
    if (logoutBtn) logoutBtn.style.display = 'none';
  }
}

function renderSummary(summary) {
  const ordersEl = document.getElementById('stat-orders');
  const revenueEl = document.getElementById('stat-revenue');
  const bestSellers = document.getElementById('best-sellers');
  if (ordersEl) ordersEl.textContent = summary.total_orders || 0;
  if (revenueEl) revenueEl.textContent = formatCurrency(summary.total_revenue || 0);
  if (bestSellers) {
    bestSellers.innerHTML = summary.best_sellers.map(item => `
      <div class="panel-card">
        <div>
          <strong>${item.product_name}</strong>
          <span>${item.total_quantity} sold</span>
        </div>
        <span>${formatCurrency(item.total_revenue)}</span>
      </div>
    `).join('');
  }
}

function renderProductAdminTable(products) {
  const container = document.getElementById('product-admin-table');
  if (!container) return;
  container.innerHTML = `
    <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
      <h3>All Products</h3>
      <button id="show-add-product" class="btn btn-primary btn-sm">+ Add Product</button>
    </div>
    <div id="add-product-form" class="admin-create-form" style="display:none;">
      <div>
        <label>Title</label>
        <input id="new-product-title" placeholder="Product name" />
      </div>
      <div>
        <label>Price</label>
        <input id="new-product-price" type="number" step="0.01" placeholder="0.00" />
      </div>
      <div>
        <label>Stock</label>
        <input id="new-product-stock" type="number" placeholder="0" />
      </div>
      <div>
        <label>Category ID</label>
        <input id="new-product-category" type="number" placeholder="1" />
      </div>
      <div class="full-width">
        <label>Description</label>
        <textarea id="new-product-description" rows="2" placeholder="Product description"></textarea>
      </div>
      <div class="full-width">
        <label>Image URL</label>
        <input id="new-product-image" placeholder="https://..." />
      </div>
      <div class="full-width" style="display:flex;gap:8px;align-items:center;">
        <label style="margin-bottom:0;">
          <input id="new-product-featured" type="checkbox" /> Featured
        </label>
        <button id="save-new-product" class="btn btn-primary btn-sm">Save Product</button>
        <button id="cancel-add-product" class="btn btn-outline btn-sm">Cancel</button>
      </div>
    </div>
    <table>
      <thead>
        <tr><th>ID</th><th>Title</th><th>Stock</th><th>Price</th><th>Featured</th><th>Actions</th></tr>
      </thead>
      <tbody>
        ${products.map(product => `
          <tr data-product-id="${product.id}">
            <td>${product.id}</td>
            <td>${product.title}</td>
            <td><input type="number" min="0" value="${product.stock}" class="admin-stock" style="width:80px;padding:8px;border-radius:10px;border:1px solid var(--border);" /></td>
            <td>${formatCurrency(product.price)}</td>
            <td><input type="checkbox" class="admin-featured" ${product.featured ? 'checked' : ''} /></td>
            <td style="display:flex;gap:8px;">
              <button class="btn btn-sm btn-primary update-product">Save</button>
              <button class="btn btn-sm btn-danger delete-product">Delete</button>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  // Add product toggle
  document.getElementById('show-add-product')?.addEventListener('click', () => {
    const form = document.getElementById('add-product-form');
    form.style.display = form.style.display === 'none' ? 'grid' : 'none';
  });
  document.getElementById('cancel-add-product')?.addEventListener('click', () => {
    document.getElementById('add-product-form').style.display = 'none';
  });
  document.getElementById('save-new-product')?.addEventListener('click', async () => {
    const title = document.getElementById('new-product-title').value.trim();
    const price = parseFloat(document.getElementById('new-product-price').value);
    const stock = parseInt(document.getElementById('new-product-stock').value) || 0;
    const category_id = parseInt(document.getElementById('new-product-category').value) || null;
    const description = document.getElementById('new-product-description').value.trim();
    const image = document.getElementById('new-product-image').value.trim();
    const featured = document.getElementById('new-product-featured').checked;
    if (!title || !price) {
      showToast('Title and price are required', 'warning');
      return;
    }
    try {
      await apiFetch('/products', {
        method: 'POST',
        body: { title, price, stock, category_id, description, image, featured }
      });
      showToast('Product created successfully', 'success');
      document.getElementById('add-product-form').style.display = 'none';
      await loadAdminProducts();
    } catch (err) {
      showToast(err.body?.detail || err.message || 'Failed to create product', 'error');
    }
  });

  container.querySelectorAll('.update-product').forEach(button => {
    button.addEventListener('click', async (event) => {
      const row = event.target.closest('tr');
      const productId = Number(row.dataset.productId);
      const stock = Number(row.querySelector('.admin-stock').value);
      const featured = row.querySelector('.admin-featured').checked;
      try {
        await apiFetch(`/products/${productId}`, {
          method: 'PUT',
          body: { stock, featured }
        });
        showToast('Product updated successfully', 'success');
        await loadAdminProducts();
      } catch (err) {
        showToast(err.body?.detail || err.message || 'Update failed', 'error');
      }
    });
  });

  container.querySelectorAll('.delete-product').forEach(button => {
    button.addEventListener('click', async (event) => {
      const row = event.target.closest('tr');
      const productId = Number(row.dataset.productId);
      if (!confirm('Delete this product?')) return;
      try {
        await apiFetch(`/products/${productId}`, { method: 'DELETE' });
        showToast('Product deleted', 'success');
        await loadAdminProducts();
      } catch (err) {
        showToast(err.body?.detail || err.message || 'Delete failed', 'error');
      }
    });
  });
}

function renderOrderAdminTable(orders) {
  const container = document.getElementById('order-admin-table');
  if (!container) return;
  container.innerHTML = `
    <h3>All Orders</h3>
    <table>
      <thead>
        <tr><th>ID</th><th>Customer</th><th>Items</th><th>Qty</th><th>Total</th><th>Status</th><th>Actions</th></tr>
      </thead>
      <tbody>
        ${orders.map(order => `
          <tr data-order-id="${order.id}">
            <td>${order.id}</td>
            <td>${order.customer}</td>
            <td>${order.items ? order.items.map(i => i.product_name).join(', ') : order.product_name || '-'}</td>
            <td>${order.items ? order.items.reduce((s, i) => s + i.quantity, 0) : order.quantity || 0}</td>
            <td>${formatCurrency(order.total_price)}</td>
            <td>
              <select class="order-status">
                <option value="pending" ${order.status === 'pending' ? 'selected' : ''}>pending</option>
                <option value="processing" ${order.status === 'processing' ? 'selected' : ''}>processing</option>
                <option value="shipped" ${order.status === 'shipped' ? 'selected' : ''}>shipped</option>
                <option value="delivered" ${order.status === 'delivered' ? 'selected' : ''}>delivered</option>
                <option value="cancelled" ${order.status === 'cancelled' ? 'selected' : ''}>cancelled</option>
              </select>
            </td>
            <td>
              <div style="display:flex;gap:8px;">
                <button class="btn btn-sm btn-primary save-status">Update</button>
                <button class="btn btn-sm btn-outline view-shipments" data-order-id="${order.id}">Shipments</button>
              </div>
            </td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  container.querySelectorAll('.save-status').forEach(button => {
    button.addEventListener('click', async (event) => {
      const row = event.target.closest('tr');
      const orderId = Number(row.dataset.orderId);
      const status = row.querySelector('.order-status').value;
      try {
        await apiFetch(`/orders/${orderId}/status`, {
          method: 'PATCH',
          body: { status }
        });
        showToast('Order status updated', 'success');
        await loadAdminOrders();
      } catch (err) {
        showToast(err.body?.detail || err.message || 'Status update failed', 'error');
      }
    });
  });

  container.querySelectorAll('.view-shipments').forEach(button => {
    button.addEventListener('click', async (event) => {
      const orderId = Number(event.target.dataset.orderId);
      openShipmentModal(orderId);
    });
  });
}

function renderCouponAdmin(coupons) {
  const container = document.getElementById('coupon-admin-table');
  if (!container) return;
  container.innerHTML = `
    <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
      <h3>Coupons</h3>
      <button id="show-add-coupon" class="btn btn-primary btn-sm">+ Add Coupon</button>
    </div>
    <div id="add-coupon-form" class="admin-create-form" style="display:none;">
      <div>
        <label>Code</label>
        <input id="new-coupon-code" placeholder="SAVE10" />
      </div>
      <div>
        <label>Discount %</label>
        <input id="new-coupon-discount" type="number" step="0.01" placeholder="10" />
      </div>
      <div>
        <label>Max Uses</label>
        <input id="new-coupon-uses" type="number" placeholder="100" />
      </div>
      <div>
        <label>Description</label>
        <input id="new-coupon-desc" placeholder="10% off" />
      </div>
      <div class="full-width" style="display:flex;gap:8px;align-items:center;">
        <label style="margin-bottom:0;"><input id="new-coupon-active" type="checkbox" checked /> Active</label>
        <button id="save-new-coupon" class="btn btn-primary btn-sm">Save Coupon</button>
        <button id="cancel-add-coupon" class="btn btn-outline btn-sm">Cancel</button>
      </div>
    </div>
    <table>
      <thead>
        <tr><th>ID</th><th>Code</th><th>Discount</th><th>Uses</th><th>Max</th><th>Active</th><th>Expires</th><th>Actions</th></tr>
      </thead>
      <tbody>
        ${coupons.map(c => `
          <tr data-coupon-id="${c.id}">
            <td>${c.id}</td>
            <td><strong>${c.code}</strong></td>
            <td>${c.discount_percent}%</td>
            <td>${c.used_count}</td>
            <td>${c.max_uses || '∞'}</td>
            <td>${c.active ? '✓' : '✗'}</td>
            <td>${c.expires_at ? new Date(c.expires_at).toLocaleDateString() : '-'}</td>
            <td><button class="btn btn-sm btn-danger delete-coupon">Delete</button></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  document.getElementById('show-add-coupon')?.addEventListener('click', () => {
    const form = document.getElementById('add-coupon-form');
    form.style.display = form.style.display === 'none' ? 'grid' : 'none';
  });
  document.getElementById('cancel-add-coupon')?.addEventListener('click', () => {
    document.getElementById('add-coupon-form').style.display = 'none';
  });
  document.getElementById('save-new-coupon')?.addEventListener('click', async () => {
    const code = document.getElementById('new-coupon-code').value.trim().toUpperCase();
    const discount_percent = parseFloat(document.getElementById('new-coupon-discount').value) || 0;
    const max_uses = parseInt(document.getElementById('new-coupon-uses').value) || null;
    const description = document.getElementById('new-coupon-desc').value.trim() || null;
    const active = document.getElementById('new-coupon-active').checked;
    if (!code || !discount_percent) {
      showToast('Code and discount are required', 'warning');
      return;
    }
    try {
      await apiFetch('/coupons/', {
        method: 'POST',
        body: { code, discount_percent, max_uses, description, active }
      });
      showToast('Coupon created', 'success');
      document.getElementById('add-coupon-form').style.display = 'none';
      await loadAdminCoupons();
    } catch (err) {
      showToast(err.body?.detail || err.message || 'Failed to create coupon', 'error');
    }
  });

  container.querySelectorAll('.delete-coupon').forEach(btn => {
    btn.addEventListener('click', async (event) => {
      const row = event.target.closest('tr');
      const couponId = Number(row.dataset.couponId);
      if (!confirm('Delete this coupon?')) return;
      try {
        await apiFetch(`/coupons/${couponId}`, { method: 'DELETE' });
        showToast('Coupon deleted', 'success');
        await loadAdminCoupons();
      } catch (err) {
        showToast(err.body?.detail || err.message || 'Delete failed', 'error');
      }
    });
  });
}

function renderCategoryAdmin(categories) {
  const container = document.getElementById('category-admin-table');
  if (!container) return;
  container.innerHTML = `
    <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
      <h3>Categories</h3>
      <button id="show-add-category" class="btn btn-primary btn-sm">+ Add Category</button>
    </div>
    <div id="add-category-form" class="admin-create-form" style="display:none;">
      <div>
        <label>Name</label>
        <input id="new-category-name" placeholder="Category name" />
      </div>
      <div>
        <label>Description</label>
        <input id="new-category-desc" placeholder="Optional description" />
      </div>
      <div class="full-width" style="display:flex;gap:8px;">
        <button id="save-new-category" class="btn btn-primary btn-sm">Save Category</button>
        <button id="cancel-add-category" class="btn btn-outline btn-sm">Cancel</button>
      </div>
    </div>
    <table>
      <thead>
        <tr><th>ID</th><th>Name</th><th>Description</th><th>Actions</th></tr>
      </thead>
      <tbody>
        ${categories.map(c => `
          <tr data-category-id="${c.id}">
            <td>${c.id}</td>
            <td>${c.name}</td>
            <td>${c.description || '-'}</td>
            <td><button class="btn btn-sm btn-danger delete-category">Delete</button></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

  document.getElementById('show-add-category')?.addEventListener('click', () => {
    const form = document.getElementById('add-category-form');
    form.style.display = form.style.display === 'none' ? 'grid' : 'none';
  });
  document.getElementById('cancel-add-category')?.addEventListener('click', () => {
    document.getElementById('add-category-form').style.display = 'none';
  });
  document.getElementById('save-new-category')?.addEventListener('click', async () => {
    const name = document.getElementById('new-category-name').value.trim();
    const description = document.getElementById('new-category-desc').value.trim() || null;
    if (!name) {
      showToast('Category name is required', 'warning');
      return;
    }
    try {
      await apiFetch('/categories/', {
        method: 'POST',
        body: { name, description }
      });
      showToast('Category created', 'success');
      document.getElementById('add-category-form').style.display = 'none';
      await loadAdminCategories();
    } catch (err) {
      showToast(err.body?.detail || err.message || 'Failed to create category', 'error');
    }
  });

  container.querySelectorAll('.delete-category').forEach(btn => {
    btn.addEventListener('click', async (event) => {
      const row = event.target.closest('tr');
      const categoryId = Number(row.dataset.categoryId);
      if (!confirm('Delete this category?')) return;
      try {
        await apiFetch(`/categories/${categoryId}`, { method: 'DELETE' });
        showToast('Category deleted', 'success');
        await loadAdminCategories();
      } catch (err) {
        showToast(err.body?.detail || err.message || 'Delete failed', 'error');
      }
    });
  });
}

async function loadAdminProducts() {
  const data = await apiFetch('/products?page=1&limit=100');
  adminState.products = Array.isArray(data) ? data : data.products || [];
  renderProductAdminTable(adminState.products);
}

async function loadAdminOrders() {
  adminState.orders = await apiFetch('/orders/admin/orders');
  renderOrderAdminTable(adminState.orders);
}

async function loadAdminSummary() {
  adminState.summary = await apiFetch('/orders/admin/sales-summary');
  renderSummary(adminState.summary);
}

async function loadAdminCoupons() {
  adminState.coupons = await apiFetch('/coupons/');
  renderCouponAdmin(adminState.coupons);
}

async function loadAdminCategories() {
  adminState.categories = await apiFetch('/categories/');
  renderCategoryAdmin(adminState.categories);
}

async function initializeAdminDashboard() {
  renderAdminUser();
  try {
    await Promise.all([
      loadAdminProducts(),
      loadAdminOrders(),
      loadAdminSummary(),
      loadAdminCoupons(),
      loadAdminCategories()
    ]);
  } catch (err) {
    const msg = err.body?.detail || err.message || 'Error loading dashboard';
    if (msg.includes('admin')) {
      showToast('Please sign in as admin', 'warning');
    } else {
      showToast(msg, 'error');
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('open-login')?.addEventListener('click', () => openAuthModal('login'));
  document.getElementById('admin-logout')?.addEventListener('click', () => {
    clearAuth();
    renderAdminUser();
    showToast('Logged out', 'info');
    initializeAdminDashboard();
  });
  document.getElementById('refresh-dashboard')?.addEventListener('click', initializeAdminDashboard);
  document.querySelectorAll('.modal-close').forEach(btn => btn.addEventListener('click', closeAuthModal));
  document.getElementById('login-submit')?.addEventListener('click', async (event) => {
    event.preventDefault();
    await handleLogin();
    renderAdminUser();
    closeAuthModal();
    await initializeAdminDashboard();
  });
  initializeAdminDashboard();
});

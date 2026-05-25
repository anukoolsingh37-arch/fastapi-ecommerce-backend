const adminState = {
  products: [],
  orders: [],
  summary: null
};

function formatCurrency(value) {
  return `$${Number(value).toFixed(2)}`;
}

function renderAdminUser() {
  const userLabel = document.getElementById('stat-user');
  if (!userLabel) return;
  if (state.user) {
    userLabel.textContent = `${state.user.username} (${state.user.is_admin ? 'admin' : 'user'})`;
  } else {
    userLabel.textContent = 'Not signed in';
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
            <td><button class="btn btn-sm btn-primary update-product">Save</button></td>
          </tr>
        `).join('')}
      </tbody>
    </table>
  `;

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
        alert('Product updated successfully');
        await loadAdminProducts();
      } catch (err) {
        alert(err.detail || 'Update failed');
      }
    });
  });
}

function renderOrderAdminTable(orders) {
  const container = document.getElementById('order-admin-table');
  if (!container) return;
  container.innerHTML = `
    <table>
      <thead>
        <tr><th>ID</th><th>Customer</th><th>Products</th><th>Qty</th><th>Total</th><th>Status</th><th>Actions</th></tr>
      </thead>
      <tbody>
        ${orders.map(order => `
          <tr data-order-id="${order.id}">
            <td>${order.id}</td>
            <td>${order.customer}</td>
            <td>${order.product_name}</td>
            <td>${order.quantity}</td>
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
            <td><button class="btn btn-sm btn-primary save-status">Update</button></td>
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
        alert('Order status updated');
        await loadAdminOrders();
      } catch (err) {
        alert(err.detail || 'Status update failed');
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

async function initializeAdminDashboard() {
  renderAdminUser();
  try {
    await Promise.all([loadAdminProducts(), loadAdminOrders(), loadAdminSummary()]);
  } catch (err) {
    if (err.detail) {
      alert(err.detail + ' Please sign in as admin.');
    } else {
      console.error(err);
    }
  }
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('open-login')?.addEventListener('click', () => openAuthModal('login'));
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

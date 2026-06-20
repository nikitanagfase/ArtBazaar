/**
 * artist-dashboard.js  –  Artist dashboard controller
 */

// ── Auth guard ───────────────────────────────────────────────────────────────
if (!Auth.isLoggedIn() || !Auth.isArtist()) {
  window.location.href = 'login.html';
}

const user = Auth.getUser();
document.getElementById('greetName').textContent  = user?.full_name?.split(' ')[0] || 'Artist';
document.getElementById('sideName').textContent   = user?.full_name || 'Artist';
document.getElementById('sideAvatar').textContent = getInitials(user?.full_name || 'A');

// ── Tab navigation ────────────────────────────────────────────────────────────
function showTab(name, linkEl) {
  document.querySelectorAll('.tab-content').forEach(t => t.style.display = 'none');
  document.querySelectorAll('.sidebar__link').forEach(l => l.classList.remove('active'));
  document.getElementById(`tab-${name}`).style.display = 'block';
  if (linkEl) linkEl.classList.add('active');

  if (name === 'overview')     loadOverview();
  if (name === 'artworks')     loadMyArtworks();
  if (name === 'orders')       loadIncomingOrders();
  if (name === 'commissions')  loadCommissions();
  if (name === 'profile')      loadProfile();
}

// ── Overview ──────────────────────────────────────────────────────────────────
async function loadOverview() {
  try {
    const data = await AnalyticsAPI.artist();

    // Stats
    document.getElementById('statsGrid').innerHTML = `
      <div class="stat-card stat-card--terra"><div class="stat-card__icon">🖼</div><div class="stat-card__value">${data.total_artworks}</div><div class="stat-card__label">Total Artworks</div></div>
      <div class="stat-card stat-card--amber"><div class="stat-card__icon">📦</div><div class="stat-card__value">${data.total_orders}</div><div class="stat-card__label">Total Orders</div>${data.pending_orders ? `<div class="stat-card__change">${data.pending_orders} pending</div>` : ''}</div>
      <div class="stat-card stat-card--green"><div class="stat-card__icon">💰</div><div class="stat-card__value">${formatPrice(data.total_revenue)}</div><div class="stat-card__label">Total Revenue</div></div>
      <div class="stat-card stat-card--blue"><div class="stat-card__icon">⭐</div><div class="stat-card__value">${data.average_rating || '—'}</div><div class="stat-card__label">Avg. Rating</div></div>`;

    if (data.pending_orders > 0) {
      document.getElementById('orderBadge').textContent = data.pending_orders;
      document.getElementById('orderBadge').style.display = 'flex';
    }

    // Revenue chart
    const ctx = document.getElementById('revenueChart').getContext('2d');
    const labels = data.monthly_revenue.map(r => r.month);
    const values = data.monthly_revenue.map(r => r.revenue);
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Revenue (₹)',
          data: values,
          backgroundColor: 'rgba(200,98,42,0.7)',
          borderColor: '#C8622A',
          borderWidth: 2,
          borderRadius: 6,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          y: { beginAtZero: true, ticks: { callback: v => '₹' + v.toLocaleString('en-IN') } },
          x: { grid: { display: false } }
        }
      }
    });

    // Recent orders
    const roEl = document.getElementById('recentOrders');
    if (!data.recent_orders?.length) {
      roEl.innerHTML = '<p class="text-muted">No orders yet.</p>';
    } else {
      roEl.innerHTML = data.recent_orders.map(o => orderCardHTML(o)).join('');
    }
  } catch (err) {
    showToast('Could not load analytics — is the backend running?', 'error');
  }
}

// ── My Artworks ───────────────────────────────────────────────────────────────
async function loadMyArtworks() {
  const grid = document.getElementById('myArtworkGrid');
  grid.innerHTML = skeletonCards(6);
  try {
    const artworks = await ArtworkAPI.list({ artist_id: user.id, limit: 50 });
    if (!artworks.length) {
      grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:60px;">
        <div style="font-size:3rem;margin-bottom:16px;">🎨</div>
        <h3>No artworks yet</h3>
        <p class="text-muted" style="margin-bottom:20px;">Upload your first artwork to get started.</p>
        <button class="btn btn-primary" onclick="showTab('upload',document.querySelector('[onclick*=upload]'))">Upload Artwork</button>
      </div>`;
      return;
    }
    grid.innerHTML = artworks.map(a => `
      <div class="artwork-card">
        <div class="artwork-card__image-wrap">
          <img src="${artworkImg(a.image_urls, a.title)}" alt="${a.title}" loading="lazy"/>
          <span class="artwork-card__badge">${a.is_available ? 'Available' : 'Sold Out'}</span>
        </div>
        <div class="artwork-card__body">
          <div class="artwork-card__category">${a.category}</div>
          <div class="artwork-card__title">${a.title}</div>
          <div class="artwork-card__footer">
            <div class="artwork-card__price">${formatPrice(a.price)}</div>
            <div style="display:flex;gap:6px;">
              <a href="artwork-detail.html?id=${a.id}" class="btn btn-ghost btn-sm">View</a>
              <button class="btn btn-sm" style="background:#fee2e2;color:#991b1b;border:none;" onclick="deleteArtwork(${a.id},this)">Del</button>
            </div>
          </div>
        </div>
      </div>`).join('');
  } catch (err) {
    grid.innerHTML = '<p class="text-muted">Failed to load artworks.</p>';
  }
}

async function deleteArtwork(id, btn) {
  if (!confirm('Delete this artwork?')) return;
  try {
    await ArtworkAPI.delete(id);
    showToast('Artwork deleted', 'success');
    loadMyArtworks();
  } catch (err) { showToast(err.message, 'error'); }
}

// ── Upload Artwork ─────────────────────────────────────────────────────────────
let selectedFiles = [];

document.getElementById('imgFiles')?.addEventListener('change', (e) => {
  selectedFiles = Array.from(e.target.files);
  renderPreviews();
});

const zone = document.getElementById('uploadZone');
if (zone) {
  zone.addEventListener('dragover',  e => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', e => {
    e.preventDefault();
    zone.classList.remove('dragover');
    selectedFiles = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
    renderPreviews();
  });
}

function renderPreviews() {
  const grid = document.getElementById('imgPreview');
  grid.innerHTML = selectedFiles.map((f, i) => {
    const url = URL.createObjectURL(f);
    return `<div class="image-preview-item"><img src="${url}"/><button class="image-preview-item__remove" onclick="removePreview(${i})">✕</button></div>`;
  }).join('');
}

function removePreview(idx) {
  selectedFiles.splice(idx, 1);
  renderPreviews();
}

async function generateAIDesc() {
  if (!selectedFiles.length) { showToast('Please select an image first', 'info'); return; }
  showToast('🤖 Generating AI description…', 'info', 8000);
  const fd = new FormData();
  fd.append('file', selectedFiles[0]);
  try {
    const data = await AIAPI.generateDesc(fd);
    document.getElementById('aw_title').value = data.title;
    document.getElementById('aw_desc').value  = data.description;
    document.getElementById('aw_tags').value  = data.tags.join(', ');
    showToast('AI description generated! ✨', 'success');
  } catch (err) {
    showToast('AI generation failed: ' + err.message, 'error');
  }
}

async function submitArtwork() {
  const title    = document.getElementById('aw_title').value.trim();
  const category = document.getElementById('aw_cat').value;
  const price    = parseFloat(document.getElementById('aw_price').value);

  if (!title || !category || !price) { showToast('Please fill in all required fields', 'info'); return; }

  const btn = document.getElementById('submitArtworkBtn');
  btn.innerHTML = '<span class="spinner"></span> Publishing…';
  btn.disabled  = true;

  try {
    const tags = document.getElementById('aw_tags').value.split(',').map(t => t.trim()).filter(Boolean);
    const artwork = await ArtworkAPI.create({
      title, category, price,
      description: document.getElementById('aw_desc').value.trim(),
      medium:      document.getElementById('aw_medium').value.trim(),
      dimensions:  document.getElementById('aw_dims').value.trim(),
      stock:       parseInt(document.getElementById('aw_stock').value) || 1,
      tags,
    });

    // Upload images
    if (selectedFiles.length) {
      const fd = new FormData();
      selectedFiles.forEach(f => fd.append('files', f));
      await ArtworkAPI.uploadImages(artwork.id, fd);
    }

    showToast(`"${artwork.title}" published! 🎉`, 'success');
    selectedFiles = [];
    renderPreviews();
    ['aw_title','aw_desc','aw_price','aw_medium','aw_dims','aw_tags'].forEach(id => document.getElementById(id).value = '');
    document.getElementById('aw_cat').value = '';
    showTab('artworks', document.querySelector('[onclick*=artworks]'));

  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    btn.innerHTML = 'Publish Artwork';
    btn.disabled  = false;
  }
}

// ── Incoming Orders ───────────────────────────────────────────────────────────
async function loadIncomingOrders() {
  const el = document.getElementById('incomingOrders');
  el.innerHTML = '<div class="spinner" style="margin:40px auto;display:block;"></div>';
  try {
    const orders = await OrderAPI.incomingOrders();
    if (!orders.length) { el.innerHTML = '<p class="text-muted">No orders yet.</p>'; return; }
    el.innerHTML = orders.map(o => orderCardHTML(o, true)).join('');
  } catch (err) { el.innerHTML = '<p class="text-muted">Failed to load orders.</p>'; }
}

function orderCardHTML(o, withActions = false) {
  const STATUSES = ['pending','confirmed','shipped','delivered','cancelled'];
  return `<div class="order-card">
    <div class="order-card__header">
      <div><div class="order-card__id">Order #${o.id}</div><div class="order-card__date">${formatDate(o.created_at)}</div></div>
      <span class="badge badge-${o.status}">${o.status}</span>
    </div>
    <div class="order-card__body">
      <div class="order-card__items">
        ${(o.items||[]).map(i=>`<div class="order-item">
          <img class="order-item__thumb" src="${artworkImg(i.artwork?.image_urls, i.artwork?.title)}" alt=""/>
          <div><div class="order-item__name">${i.artwork?.title||'Artwork'}</div><div class="order-item__qty">Qty: ${i.quantity}</div></div>
          <div class="order-item__price">${formatPrice(i.unit_price * i.quantity)}</div>
        </div>`).join('')}
      </div>
    </div>
    <div class="order-card__footer">
      <div class="order-card__total">Total: ${formatPrice(o.total_amount)}</div>
      ${withActions ? `<select class="form-select" style="width:auto;font-size:0.85rem;" onchange="updateOrderStatus(${o.id},this.value)">
        ${STATUSES.map(s=>`<option value="${s}" ${s===o.status?'selected':''}>${s.charAt(0).toUpperCase()+s.slice(1)}</option>`).join('')}
      </select>` : ''}
    </div>
  </div>`;
}

async function updateOrderStatus(orderId, status) {
  try {
    await OrderAPI.updateStatus(orderId, status);
    showToast(`Order #${orderId} updated to "${status}"`, 'success');
  } catch (err) { showToast(err.message, 'error'); }
}

// ── Commissions ───────────────────────────────────────────────────────────────
async function loadCommissions() {
  const el = document.getElementById('commissionList');
  el.innerHTML = '<div class="spinner" style="margin:40px auto;display:block;"></div>';
  try {
    const commissions = await CommissionAPI.incoming();
    if (!commissions.length) { el.innerHTML = '<p class="text-muted">No commission requests yet.</p>'; return; }
    el.innerHTML = commissions.map(c => `
      <div class="commission-card">
        <div style="display:flex;align-items:start;justify-content:space-between;gap:12px;">
          <div>
            <div class="commission-card__title">${c.title}</div>
            <div class="commission-card__meta">
              <span>👤 ${c.buyer?.full_name}</span>
              ${c.budget ? `<span>💰 Budget: ${formatPrice(c.budget)}</span>` : ''}
              ${c.deadline ? `<span>📅 By ${formatDate(c.deadline)}</span>` : ''}
            </div>
            <p style="font-size:0.9rem;color:var(--ink-mid);line-height:1.7;">${c.description}</p>
          </div>
          <span class="badge badge-${c.status==='pending'?'pending':c.status==='accepted'?'confirmed':'delivered'}">${c.status}</span>
        </div>
        ${c.status === 'pending' ? `
        <div style="margin-top:16px;display:flex;gap:10px;">
          <button class="btn btn-primary btn-sm" onclick="respondCommission(${c.id},'accepted')">Accept</button>
          <button class="btn btn-ghost btn-sm" onclick="respondCommission(${c.id},'rejected')">Decline</button>
        </div>` : ''}
        ${c.status === 'accepted' ? `
        <div style="margin-top:16px;">
          <input type="number" class="form-input" id="price_${c.id}" placeholder="Agreed price (₹)" style="max-width:200px;margin-bottom:8px;" />
          <button class="btn btn-primary btn-sm" onclick="setPrice(${c.id})">Set Price & Start</button>
        </div>` : ''}
      </div>`).join('');
  } catch (err) { el.innerHTML = '<p class="text-muted">Failed to load commissions.</p>'; }
}

async function respondCommission(id, status) {
  try {
    await CommissionAPI.update(id, { status });
    showToast(`Commission ${status}!`, 'success');
    loadCommissions();
  } catch (err) { showToast(err.message, 'error'); }
}

async function setPrice(id) {
  const price = parseFloat(document.getElementById(`price_${id}`).value);
  if (!price) { showToast('Please enter a price', 'info'); return; }
  try {
    await CommissionAPI.update(id, { status: 'in_progress', agreed_price: price });
    showToast('Commission started!', 'success');
    loadCommissions();
  } catch (err) { showToast(err.message, 'error'); }
}

// ── Profile ───────────────────────────────────────────────────────────────────
function loadProfile() {
  const user = Auth.getUser();
  document.getElementById('p_name').value = user?.full_name || '';
  document.getElementById('p_bio').value  = user?.bio || '';
  document.getElementById('p_loc').value  = user?.location || '';
}

async function updateProfile() {
  try {
    const updated = await AuthAPI.updateMe({
      full_name: document.getElementById('p_name').value.trim(),
      bio:       document.getElementById('p_bio').value.trim(),
      location:  document.getElementById('p_loc').value.trim(),
    });
    Auth.setUser({ ...Auth.getUser(), ...updated });
    document.getElementById('sideName').textContent = updated.full_name;
    showToast('Profile updated!', 'success');
  } catch (err) { showToast(err.message, 'error'); }
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function skeletonCards(n) {
  return Array(n).fill(`<div class="artwork-card"><div class="skeleton" style="height:200px;"></div><div style="padding:16px"><div class="skeleton" style="height:14px;margin-bottom:8px;"></div><div class="skeleton" style="height:12px;width:60%;"></div></div></div>`).join('');
}

// ── Init ──────────────────────────────────────────────────────────────────────
showTab('overview', document.querySelector('[onclick*=overview]'));

/**
 * api.js  –  ArtBazaar centralised API client.
 * All fetch calls go through here for consistent token handling and error toasting.
 */

const API_BASE  = "https://artbazaar.onrender.com/api";


// ── Token helpers ──────────────────────────────────────────────────────────
const Auth = {
  getToken:  () => localStorage.getItem('artbazaar_token'),
  setToken:  (t) => localStorage.setItem('artbazaar_token', t),
  clearToken:() => localStorage.removeItem('artbazaar_token'),
  getUser:   () => {
    try { return JSON.parse(localStorage.getItem('artbazaar_user') || 'null'); }
    catch { return null; }
  },
  setUser:   (u) => localStorage.setItem('artbazaar_user', JSON.stringify(u)),
  clearUser: () => localStorage.removeItem('artbazaar_user'),
  isLoggedIn:() => !!Auth.getToken(),
  isArtist:  () => Auth.getUser()?.role === 'artist',
  isBuyer:   () => Auth.getUser()?.role === 'buyer',
  logout: () => {
  Auth.clearToken();
  Auth.clearUser();
  window.location.href = '/index.html';
}
};

// ── Core fetch wrapper ─────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const token = Auth.getToken();
  const headers = { ...(options.headers || {}) };

  // Only set JSON content-type when not sending FormData
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    Auth.logout();
    throw new Error('Session expired. Please login again.');
  }

  const data = res.headers.get('content-type')?.includes('application/json')
    ? await res.json()
    : await res.text();

  if (!res.ok) {
    const msg = data?.detail || data?.message || 'An error occurred';
    throw new Error(Array.isArray(msg) ? msg.map(e => e.msg).join(', ') : msg);
  }

  return data;
}

// ── Auth API ────────────────────────────────────────────────────────────────
const AuthAPI = {
  register: (payload) => apiFetch('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  login:    (payload) => apiFetch('/auth/login',    { method: 'POST', body: JSON.stringify(payload) }),
  getMe:    ()        => apiFetch('/auth/me'),
  updateMe: (payload) => apiFetch('/auth/me', { method: 'PUT', body: JSON.stringify(payload) }),
  getNotifications: () => apiFetch('/auth/me/notifications'),
  markNotifRead: (id) => apiFetch(`/auth/me/notifications/${id}/read`, { method: 'PUT' }),
};

// ── Artwork API ─────────────────────────────────────────────────────────────
const ArtworkAPI = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return apiFetch(`/artworks${qs ? '?' + qs : ''}`);
  },
  featured:   () => apiFetch('/artworks/featured'),
  get:        (id) => apiFetch(`/artworks/${id}`),
  create:     (payload) => apiFetch('/artworks', { method: 'POST', body: JSON.stringify(payload) }),
  update:     (id, payload) => apiFetch(`/artworks/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  delete:     (id) => apiFetch(`/artworks/${id}`, { method: 'DELETE' }),
  uploadImages: (id, formData) => apiFetch(`/artworks/${id}/images`, { method: 'POST', body: formData }),
  deleteImage:  (id, idx)    => apiFetch(`/artworks/${id}/images/${idx}`, { method: 'DELETE' }),
  getReviews:   (id)         => apiFetch(`/artworks/${id}/reviews`),
  addReview:    (id, payload)=> apiFetch(`/artworks/${id}/reviews`, { method: 'POST', body: JSON.stringify(payload) }),
  addWishlist:  (id)         => apiFetch(`/artworks/${id}/wishlist`, { method: 'POST' }),
  removeWishlist:(id)        => apiFetch(`/artworks/${id}/wishlist`, { method: 'DELETE' }),
};

// ── Order API ───────────────────────────────────────────────────────────────
const OrderAPI = {
  placeOrder:    (payload)     => apiFetch('/orders',            { method: 'POST', body: JSON.stringify(payload) }),
  myOrders:      ()            => apiFetch('/orders/my'),
  myWishlist:    ()            => apiFetch('/orders/my/wishlist'),
  incomingOrders:()            => apiFetch('/orders/incoming'),
  getOrder:      (id)          => apiFetch(`/orders/${id}`),
  updateStatus:  (id, status)  => apiFetch(`/orders/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) }),
};

// ── Custom Order API ────────────────────────────────────────────────────────
const CommissionAPI = {
  create:    (payload) => apiFetch('/custom-orders', { method: 'POST', body: JSON.stringify(payload) }),
  myOrders:  ()        => apiFetch('/custom-orders/my'),
  incoming:  ()        => apiFetch('/custom-orders/incoming'),
  get:       (id)      => apiFetch(`/custom-orders/${id}`),
  update:    (id, p)   => apiFetch(`/custom-orders/${id}`, { method: 'PUT', body: JSON.stringify(p) }),
  uploadRefs:(id, fd)  => apiFetch(`/custom-orders/${id}/images`, { method: 'POST', body: fd }),
};

// ── AI API ──────────────────────────────────────────────────────────────────
const AIAPI = {
  recommendations: () => apiFetch('/ai/recommendations'),
  generateDesc:    (formData) => apiFetch('/ai/generate-description', { method: 'POST', body: formData }),
  findSimilar:     (formData) => apiFetch('/ai/similar', { method: 'POST', body: formData }),
};

// ── Analytics API ────────────────────────────────────────────────────────────
const AnalyticsAPI = {
  artist: () => apiFetch('/analytics/artist'),
};

// ── Toast utility ────────────────────────────────────────────────────────────
function showToast(message, type = 'info', duration = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${icons[type] || icons.info}</span><span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(20px)';
    toast.style.transition = '0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

// ── Cart (localStorage) ──────────────────────────────────────────────────────
const Cart = {
  _key: 'artbazaar_cart',
  get: () => {
    try { return JSON.parse(localStorage.getItem(Cart._key) || '[]'); }
    catch { return []; }
  },
  save:  (items) => localStorage.setItem(Cart._key, JSON.stringify(items)),
  add: (artwork, qty = 1) => {
    const items = Cart.get();
    const existing = items.find(i => i.artwork_id === artwork.id);
    if (existing) {
      existing.quantity = Math.min(existing.quantity + qty, artwork.stock || 99);
    } else {
      items.push({ artwork_id: artwork.id, quantity: qty, artwork });
    }
    Cart.save(items);
    Cart.updateBadge();
    showToast(`"${artwork.title}" added to cart`, 'success');
  },
  remove: (artworkId) => {
    const items = Cart.get().filter(i => i.artwork_id !== artworkId);
    Cart.save(items);
    Cart.updateBadge();
  },
  clear:  () => { localStorage.removeItem(Cart._key); Cart.updateBadge(); },
  total:  () => Cart.get().reduce((s, i) => s + i.artwork.price * i.quantity, 0),
  count:  () => Cart.get().reduce((s, i) => s + i.quantity, 0),
  updateBadge: () => {
    const badge = document.querySelector('.cart-badge');
    if (badge) {
      const count = Cart.count();
      badge.textContent = count;
      badge.style.display = count > 0 ? 'flex' : 'none';
    }
  },
};

// ── Format helpers ────────────────────────────────────────────────────────────
function formatPrice(amount, currency = '₹') {
  return `${currency}${Number(amount).toLocaleString('en-IN', { minimumFractionDigits: 0 })}`;
}

function formatDate(isoStr) {
  if (!isoStr) return '—';
  return new Date(isoStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

function getInitials(name = '') {
  return name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);
}

function ratingStars(rating, max = 5) {
  return Array.from({ length: max }, (_, i) => i < rating ? '★' : '☆').join('');
}

function debounce(fn, delay = 300) {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), delay); };
}

// ── Artwork placeholder image ────────────────────────────────────────────────
function artworkImg(urls, title = '') {
  const placeholder = `https://placehold.co/400x300/F0EBE1/C8622A?text=${encodeURIComponent(title || 'Art')}`;
  return urls && urls.length > 0 ? `${API_BASE}${urls[0]}` : placeholder;
}

// ── Navbar scroll effect ────────────────────────────────────────────────────
window.addEventListener('scroll', () => {
  document.querySelector('.navbar')?.classList.toggle('scrolled', window.scrollY > 20);
});

// Export to global scope
window.API_BASE = API_BASE;
window.Auth = Auth;
window.AuthAPI = AuthAPI;
window.ArtworkAPI = ArtworkAPI;
window.OrderAPI = OrderAPI;
window.CommissionAPI = CommissionAPI;
window.AIAPI = AIAPI;
window.AnalyticsAPI = AnalyticsAPI;
window.Cart = Cart;
window.showToast = showToast;
window.formatPrice = formatPrice;
window.formatDate = formatDate;
window.getInitials = getInitials;
window.ratingStars = ratingStars;
window.debounce = debounce;
window.artworkImg = artworkImg;
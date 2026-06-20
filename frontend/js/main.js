/**
 * main.js  –  Homepage controller
 */

// ── Navbar Actions ──────────────────────────────────────────────────────────
function renderNavActions() {
  const el = document.getElementById('navActions');
  if (!el) return;

  if (typeof Auth === 'undefined') {
    el.innerHTML = '<a href="pages/login.html" class="btn btn-ghost btn-sm">Sign In</a>' +
                   '<a href="pages/register.html" class="btn btn-primary btn-sm">Join Free</a>';
    return;
  }

  if (Auth.isLoggedIn()) {
    const user = Auth.getUser();
    const dashLink = user && user.role === 'artist'
      ? 'pages/artist-dashboard.html'
      : 'pages/buyer-dashboard.html';

    const avatarHTML = user && user.avatar_url
      ? '<img src="' + API_BASE + user.avatar_url + '" alt="">'
      : getInitials((user && user.full_name) || 'U');

    const firstName = (user && user.full_name)
      ? user.full_name.split(' ')[0]
      : 'Account';

    el.innerHTML =
      '<a href="pages/cart.html" class="btn btn-ghost btn-sm" style="position:relative;">' +
        '🛒 Cart' +
        '<span class="cart-badge" style="position:absolute;top:-6px;right:-6px;background:var(--terracotta);color:white;border-radius:50%;width:18px;height:18px;font-size:0.65rem;display:none;align-items:center;justify-content:center;font-weight:700;">0</span>' +
      '</a>' +
      '<a href="' + dashLink + '" style="display:flex;align-items:center;gap:8px;font-weight:500;color:var(--ink-mid);font-size:0.9rem;">' +
        '<div class="navbar__avatar">' + avatarHTML + '</div>' +
        '<span class="hide-mobile">' + firstName + '</span>' +
      '</a>';

  } else {
    el.innerHTML =
      '<a href="pages/login.html" class="btn btn-ghost btn-sm">Sign In</a>' +
      '<a href="pages/register.html" class="btn btn-primary btn-sm">Join Free</a>';
  }

  if (typeof Cart !== 'undefined') Cart.updateBadge();
}

// ── Categories ──────────────────────────────────────────────────────────────
const CATEGORIES = [
  { id: 'painting',    label: 'Paintings',    emoji: '🖼️',  color: '#C8622A' },
  { id: 'sculpture',   label: 'Sculptures',   emoji: '🗿',  color: '#9E4A1A' },
  { id: 'photography', label: 'Photography',  emoji: '📷',  color: '#7B5C2E' },
  { id: 'digital',     label: 'Digital Art',  emoji: '💻',  color: '#4A6741' },
  { id: 'textile',     label: 'Textile Art',  emoji: '🧵',  color: '#5B4B8A' },
  { id: 'ceramics',    label: 'Ceramics',     emoji: '🏺',  color: '#B05E38' },
  { id: 'jewellery',   label: 'Jewellery',    emoji: '💎',  color: '#2E7D8C' },
  { id: 'other',       label: 'Other',        emoji: '✨',  color: '#6B6B6B' },
];

function renderCategories() {
  const grid = document.getElementById('categoryGrid');
  if (!grid) return;
  grid.innerHTML = CATEGORIES.map(c => `
    <a href="pages/marketplace.html?category=${c.id}"
       class="card"
       style="padding:28px 20px;text-align:center;cursor:pointer;text-decoration:none;">
      <div style="font-size:2.2rem;margin-bottom:12px;">${c.emoji}</div>
      <div style="font-family:'Playfair Display',serif;font-size:1rem;font-weight:600;color:var(--ink);margin-bottom:4px;">${c.label}</div>
      <div style="font-size:0.8rem;color:var(--terracotta);">Browse →</div>
    </a>`).join('');
}

// ── Featured Artworks ───────────────────────────────────────────────────────
async function renderFeatured() {
  const grid = document.getElementById('featuredGrid');
  if (!grid) return;
  try {
    const artworks = await ArtworkAPI.featured();
    if (!artworks.length) {
      grid.innerHTML = '<p style="color:var(--ink-soft);grid-column:1/-1;text-align:center;padding:40px 0;">No featured artworks yet. Check back soon!</p>';
      return;
    }
    grid.innerHTML = artworks.map(a => artworkCardHTML(a)).join('');
    grid.querySelectorAll('.artwork-card').forEach(card => {
      card.addEventListener('click', (e) => {
        if (e.target.closest('.artwork-card__wishlist')) return;
        window.location.href = `pages/artwork-detail.html?id=${card.dataset.id}`;
      });
    });
    grid.querySelectorAll('.artwork-card__wishlist').forEach(btn => {
      btn.addEventListener('click', () => handleWishlist(btn));
    });
  } catch (err) {
    grid.innerHTML = '<p style="color:var(--ink-soft);grid-column:1/-1;text-align:center;padding:40px 0;">Could not load artworks. Make sure the backend is running.</p>';
  }
}

function artworkCardHTML(a) {
  return `
    <div class="artwork-card" data-id="${a.id}">
      <div class="artwork-card__image-wrap">
        <img src="${artworkImg(a.image_urls, a.title)}" alt="${a.title}" loading="lazy"/>
        ${a.is_featured ? '<span class="artwork-card__badge">Featured</span>' : ''}
        <button class="artwork-card__wishlist" data-id="${a.id}" aria-label="Wishlist">♡</button>
        <div class="artwork-card__overlay">
          <div class="btn btn-sm btn-amber">View Details</div>
        </div>
      </div>
      <div class="artwork-card__body">
        <div class="artwork-card__category">${a.category}</div>
        <div class="artwork-card__title">${a.title}</div>
        <div class="artwork-card__artist">by ${a.artist?.full_name || 'Unknown Artist'}</div>
        <div class="artwork-card__footer">
          <div class="artwork-card__price">${formatPrice(a.price)}</div>
          <div class="artwork-card__stars">★★★★☆</div>
        </div>
      </div>
    </div>`;
}

async function handleWishlist(btn) {
  if (!Auth.isLoggedIn()) {
    showToast('Please login to save artworks', 'info');
    return;
  }
  const id = btn.dataset.id;
  try {
    if (btn.classList.contains('active')) {
      await ArtworkAPI.removeWishlist(id);
      btn.classList.remove('active');
      btn.textContent = '♡';
      showToast('Removed from wishlist');
    } else {
      await ArtworkAPI.addWishlist(id);
      btn.classList.add('active');
      btn.textContent = '♥';
      showToast('Added to wishlist ♥', 'success');
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ── How It Works ────────────────────────────────────────────────────────────
const HOW_STEPS = [
  { icon: '✍️', title: 'Artists Upload',     text: 'Artists create a profile and upload their handmade artworks with AI-assisted descriptions and tags.' },
  { icon: '🔍', title: 'Buyers Discover',    text: 'Browse by category, search by image, or receive personalised AI recommendations tailored to your taste.' },
  { icon: '📦', title: 'Order & Receive',    text: 'Place your order securely. Track its progress and receive your unique piece of art at your doorstep.' },
];

function renderHowItWorks() {
  const grid = document.getElementById('howGrid');
  if (!grid) return;
  grid.innerHTML = HOW_STEPS.map((s, i) => `
    <div style="text-align:center;padding:32px 24px;">
      <div style="font-size:2.8rem;margin-bottom:20px;">${s.icon}</div>
      <div style="display:inline-block;width:28px;height:28px;border-radius:50%;background:var(--amber);color:var(--ink);font-weight:700;font-size:0.85rem;line-height:28px;text-align:center;margin-bottom:16px;">${i + 1}</div>
      <h3 style="color:var(--white);margin-bottom:12px;">${s.title}</h3>
      <p style="color:rgba(250,247,242,0.65);font-size:0.95rem;line-height:1.7;">${s.text}</p>
    </div>`).join('');
}

// ── AI Features ─────────────────────────────────────────────────────────────
const AI_FEATURES = [
  { icon: '🤖', title: 'Smart Recommendations', text: 'AI analyses your browsing and purchase history to surface art you\'ll love.' },
  { icon: '✍️', title: 'Auto Descriptions',     text: 'Artists upload images and get AI-generated titles, descriptions, and tags instantly.' },
  { icon: '🔎', title: 'Visual Search',          text: 'Upload any image and find visually similar artworks using CLIP embedding search.' },
];

function renderAIFeatures() {
  const el = document.getElementById('aiFeatures');
  if (!el) return;
  el.innerHTML = AI_FEATURES.map(f => `
    <div style="display:flex;align-items:flex-start;gap:16px;">
      <div style="width:44px;height:44px;border-radius:12px;background:rgba(200,98,42,0.1);display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0;">${f.icon}</div>
      <div>
        <div style="font-weight:600;color:var(--ink);margin-bottom:4px;">${f.title}</div>
        <div style="font-size:0.9rem;color:var(--ink-soft);line-height:1.6;">${f.text}</div>
      </div>
    </div>`).join('');
}

// ── Testimonials ────────────────────────────────────────────────────────────
//const TESTIMONIALS = [
//  { name: 'Priya Sharma',   role: 'Art Collector, Mumbai',    text: 'ArtBazaar helped me find a stunning original painting for my living room. The image search feature is incredible!', rating: 5, avatar: '🎨' },
//  { name: 'Rajan Mehta',    role: 'Artist, Jaipur',           text: 'I sold my first artwork within a week of joining. The AI description tool saved me hours of writing!', rating: 5, avatar: '🖌️' },
//  { name: 'Anika Verma',    role: 'Interior Designer, Delhi',  text: 'The custom commission feature is a game-changer. I requested a bespoke piece and the artist delivered beyond expectations.', rating: 5, avatar: '✨' },
//];

function renderTestimonials() {
  const grid = document.getElementById('testimonialGrid');
  if (!grid) return;
  grid.innerHTML = TESTIMONIALS.map(t => `
    <div class="card" style="padding:32px;">
      <div style="color:var(--amber);font-size:1.1rem;margin-bottom:16px;">${'★'.repeat(t.rating)}</div>
      <p style="font-size:0.95rem;line-height:1.8;color:var(--ink-mid);margin-bottom:24px;font-style:italic;">"${t.text}"</p>
      <div style="display:flex;align-items:center;gap:12px;">
        <div style="width:44px;height:44px;border-radius:50%;background:var(--cream-dark);display:flex;align-items:center;justify-content:center;font-size:1.4rem;">${t.avatar}</div>
        <div>
          <div style="font-weight:600;color:var(--ink);font-size:0.95rem;">${t.name}</div>
          <div style="font-size:0.8rem;color:var(--ink-soft);">${t.role}</div>
        </div>
      </div>
    </div>`).join('');
}

// ── Nav Search ──────────────────────────────────────────────────────────────
document.getElementById('navSearch')?.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') {
    window.location.href = `pages/marketplace.html?q=${encodeURIComponent(e.target.value)}`;
  }
});

// ── Init ─────────────────────────────────────────────────────────────────────
renderNavActions();
renderCategories();
renderFeatured();
renderHowItWorks();
renderAIFeatures();
renderTestimonials();

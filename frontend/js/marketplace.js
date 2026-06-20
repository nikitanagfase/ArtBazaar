/**
 * marketplace.js  –  Marketplace page controller
 */

// ── State ───────────────────────────────────────────────────────────────────
const state = {
  page:     1,
  limit:    12,
  category: '',
  sortBy:   'created_at',
  order:    'desc',
  minPrice: 0,
  maxPrice: 50000,
  q:        '',
  loading:  false,
  total:    0,
};

// ── Nav ─────────────────────────────────────────────────────────────────────
(function renderNav() {
  const el = document.getElementById('navActions');
  if (!el) return;

  // Guard in case api.js failed to load
  if (typeof Auth === 'undefined') {
    el.innerHTML = `<a href="login.html" class="btn btn-ghost btn-sm">Sign In</a><a href="register.html" class="btn btn-primary btn-sm">Join Free</a>`;
    return;
  }

  if (Auth.isLoggedIn()) {
    const user = Auth.getUser();
    const dash = user?.role === 'artist' ? 'artist-dashboard.html' : 'buyer-dashboard.html';
    el.innerHTML = `
      <a href="cart.html" class="btn btn-ghost btn-sm" style="position:relative;">
        🛒
        <span class="cart-badge" style="position:absolute;top:-6px;right:-6px;background:var(--terracotta);color:white;border-radius:50%;width:18px;height:18px;font-size:0.65rem;display:none;align-items:center;justify-content:center;font-weight:700;"></span>
      </a>
      <a href="${dash}" class="btn btn-ghost btn-sm">${getInitials(user?.full_name)} Dashboard</a>`;
  } else {
    el.innerHTML = `<a href="login.html" class="btn btn-ghost btn-sm">Sign In</a><a href="register.html" class="btn btn-primary btn-sm">Join Free</a>`;
  }

  if (typeof Cart !== 'undefined') Cart.updateBadge();
})();

// ── Parse URL params ─────────────────────────────────────────────────────────
const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('q'))        { state.q        = urlParams.get('q'); document.getElementById('searchInput').value = state.q; }
if (urlParams.get('category')) { state.category = urlParams.get('category'); }

// ── Category chips ───────────────────────────────────────────────────────────
document.querySelectorAll('.filter-chip').forEach(chip => {
  if (chip.dataset.cat === state.category) chip.classList.add('active');
  chip.addEventListener('click', () => {
    document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');
    state.category = chip.dataset.cat;
    state.page = 1;
    loadArtworks(true);
  });
});

// ── Sort ─────────────────────────────────────────────────────────────────────
document.getElementById('sortSelect').addEventListener('change', (e) => {
  const [sortBy, order] = e.target.value.split('|');
  state.sortBy = sortBy;
  state.order  = order;
  state.page   = 1;
  loadArtworks(true);
});

// ── Price range ───────────────────────────────────────────────────────────────
const minSlider = document.getElementById('minPrice');
const maxSlider = document.getElementById('maxPrice');
const debouncedFilter = debounce(() => { state.page = 1; loadArtworks(true); }, 400);

minSlider.addEventListener('input', () => {
  if (+minSlider.value > +maxSlider.value) maxSlider.value = minSlider.value;
  state.minPrice = +minSlider.value;
  document.getElementById('minLabel').textContent = Number(minSlider.value).toLocaleString('en-IN');
  debouncedFilter();
});
maxSlider.addEventListener('input', () => {
  if (+maxSlider.value < +minSlider.value) minSlider.value = maxSlider.value;
  state.maxPrice = +maxSlider.value;
  document.getElementById('maxLabel').textContent = Number(maxSlider.value).toLocaleString('en-IN');
  debouncedFilter();
});

// ── Search ────────────────────────────────────────────────────────────────────
document.getElementById('searchInput').addEventListener('input', debounce((e) => {
  state.q = e.target.value.trim();
  state.page = 1;
  loadArtworks(true);
}, 350));

// ── Load artworks ─────────────────────────────────────────────────────────────
async function loadArtworks(replace = false) {
  if (state.loading) return;
  state.loading = true;

  const grid = document.getElementById('artworkGrid');
  if (replace) grid.innerHTML = skeletonCards(8);

  try {
    const params = {
      page:    state.page,
      limit:   state.limit,
      sort_by: state.sortBy,
      order:   state.order,
    };
    if (state.category)  params.category  = state.category;
    if (state.q)         params.q         = state.q;
    if (state.minPrice)  params.min_price = state.minPrice;
    if (state.maxPrice < 50000) params.max_price = state.maxPrice;

    const artworks = await ArtworkAPI.list(params);
    state.total = artworks.length;

    document.getElementById('resultCount').textContent = artworks.length;

    if (replace) grid.innerHTML = '';

    if (!artworks.length && replace) {
      grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:60px 20px;">
        <div style="font-size:3rem;margin-bottom:16px;">🎨</div>
        <h3 style="margin-bottom:8px;">No artworks found</h3>
        <p class="text-muted">Try adjusting your filters or search term.</p>
      </div>`;
    } else {
      grid.insertAdjacentHTML('beforeend', artworks.map(a => artworkCardHTML(a)).join(''));
      attachCardListeners();
    }

    document.getElementById('loadMoreWrap').style.display =
      artworks.length < state.limit ? 'none' : 'block';

  } catch (err) {
    if (replace) grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:60px;color:var(--ink-soft);">Failed to load artworks. Is the backend running?</div>`;
  } finally {
    state.loading = false;
  }
}

function loadMore() {
  state.page++;
  loadArtworks(false);
}

function clearFilters() {
  state.q = '';
  state.category = '';
  state.minPrice = 0;
  state.maxPrice = 50000;
  state.page = 1;
  document.getElementById('searchInput').value = '';
  document.getElementById('minPrice').value = 0;
  document.getElementById('maxPrice').value = 50000;
  document.getElementById('minLabel').textContent = '0';
  document.getElementById('maxLabel').textContent = '50,000';
  document.querySelectorAll('.filter-chip').forEach((c, i) => c.classList.toggle('active', i === 0));
  loadArtworks(true);
}

// ── Image similarity search ──────────────────────────────────────────────────
document.getElementById('imageSearchInput').addEventListener('change', async (e) => {
  const file = e.target.files[0];
  if (!file) return;

  if (!Auth.isLoggedIn()) { showToast('Please login to use image search', 'info'); return; }

  showToast('🔍 Searching for similar artworks…', 'info', 5000);

  const fd = new FormData();
  fd.append('file', file);

  try {
    const results = await AIAPI.findSimilar(fd);
    const grid = document.getElementById('artworkGrid');
    grid.innerHTML = '';

    const banner = document.getElementById('imgSearchBanner');
    banner.style.display = 'flex';

    if (!results.length) {
      grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:60px;">No similar artworks found yet.</div>`;
      return;
    }

    grid.innerHTML = results.map(r => `
      <div class="artwork-card" data-id="${r.artwork.id}" style="position:relative;">
        ${artworkCardHTML(r.artwork)}
        <div style="position:absolute;top:52px;left:12px;background:rgba(26,20,16,0.75);color:white;border-radius:50px;padding:3px 10px;font-size:0.72rem;font-weight:600;">
          ${Math.round(r.score * 100)}% match
        </div>
      </div>`
    ).join('');

    attachCardListeners();
    document.getElementById('resultCount').textContent = results.length + ' similar';
    showToast(`Found ${results.length} similar artworks!`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
  }
});

function clearImageSearch() {
  document.getElementById('imgSearchBanner').style.display = 'none';
  document.getElementById('imageSearchInput').value = '';
  state.page = 1;
  loadArtworks(true);
}

// ── Card HTML ─────────────────────────────────────────────────────────────────
function artworkCardHTML(a) {
  return `
    <div class="artwork-card" data-id="${a.id}">
      <div class="artwork-card__image-wrap">
        <img src="${artworkImg(a.image_urls, a.title)}" alt="${a.title}" loading="lazy" />
        <button class="artwork-card__wishlist" data-id="${a.id}">♡</button>
        <div class="artwork-card__overlay">
          <div class="btn btn-sm btn-amber" style="font-size:0.78rem;">View Details</div>
        </div>
      </div>
      <div class="artwork-card__body">
        <div class="artwork-card__category">${a.category}</div>
        <div class="artwork-card__title">${a.title}</div>
        <div class="artwork-card__artist">by ${a.artist?.full_name || 'Unknown'}</div>
        <div class="artwork-card__footer">
          <div class="artwork-card__price">${formatPrice(a.price)}</div>
          <button class="btn btn-sm btn-primary" onclick="addToCart(event,${JSON.stringify(a).replace(/"/g,'&quot;')})">Add to Cart</button>
        </div>
      </div>
    </div>`;
}

function addToCart(e, artwork) {
  e.stopPropagation();
  if (!Auth.isLoggedIn()) { showToast('Please login to add to cart', 'info'); return; }
  Cart.add(artwork);
}

function attachCardListeners() {
  document.querySelectorAll('.artwork-card').forEach(card => {
    card.addEventListener('click', (e) => {
      if (e.target.closest('.artwork-card__wishlist') || e.target.closest('.btn-primary')) return;
      window.location.href = `artwork-detail.html?id=${card.dataset.id}`;
    });
  });
  document.querySelectorAll('.artwork-card__wishlist').forEach(btn => {
    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (!Auth.isLoggedIn()) { showToast('Please login to wishlist', 'info'); return; }
      try {
        if (btn.classList.contains('active')) {
          await ArtworkAPI.removeWishlist(btn.dataset.id);
          btn.classList.remove('active'); btn.textContent = '♡';
        } else {
          await ArtworkAPI.addWishlist(btn.dataset.id);
          btn.classList.add('active'); btn.textContent = '♥';
          showToast('Added to wishlist ♥', 'success');
        }
      } catch (err) { showToast(err.message, 'error'); }
    });
  });
}

function skeletonCards(n) {
  return Array(n).fill(`<div class="artwork-card"><div class="skeleton" style="height:220px;"></div><div style="padding:16px"><div class="skeleton" style="height:14px;margin-bottom:8px;"></div><div class="skeleton" style="height:12px;width:60%;"></div></div></div>`).join('');
}

// ── Init ─────────────────────────────────────────────────────────────────────
loadArtworks(true);

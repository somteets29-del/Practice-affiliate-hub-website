/* AffiliateHub — Main JS */

// ── INJECT CATEGORIES INTO NAV ──────────────────────────────────────────────
// Flask context_processor handles this server-side via @app.context_processor

// ── LIVE SEARCH AUTOCOMPLETE ─────────────────────────────────────────────────
const navInput = document.querySelector('.nav-search input');
if (navInput) {
  let timer;
  let dropdown = null;

  function createDropdown() {
    if (dropdown) return;
    dropdown = document.createElement('div');
    dropdown.style.cssText = `
      position: absolute; top: 100%; left: 0; right: 0;
      background: #1a2f45; border: 1px solid rgba(255,255,255,0.1);
      border-radius: 0 0 10px 10px; overflow: hidden; z-index: 200;
      box-shadow: 0 8px 24px rgba(0,0,0,0.3);
    `;
    const wrapper = navInput.closest('.nav-search');
    wrapper.style.position = 'relative';
    wrapper.appendChild(dropdown);
  }

  function closeDropdown() {
    if (dropdown) { dropdown.remove(); dropdown = null; }
  }

  navInput.addEventListener('input', () => {
    clearTimeout(timer);
    const q = navInput.value.trim();
    if (q.length < 2) { closeDropdown(); return; }

    timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
        const items = await res.json();
        if (!items.length) { closeDropdown(); return; }
        createDropdown();
        dropdown.innerHTML = items.map(p => `
          <a href="${p.affiliate_url}" style="
            display:flex; align-items:center; gap:0.75rem; padding:0.65rem 1rem;
            color:rgba(255,255,255,0.85); text-decoration:none; font-size:0.875rem;
            border-bottom:1px solid rgba(255,255,255,0.06); transition: background 0.12s;
          " onmouseover="this.style.background='rgba(255,255,255,0.06)'"
             onmouseout="this.style.background=''"
          >
            ${p.image_url ? `<img src="${p.image_url}" style="width:36px;height:36px;object-fit:contain;border-radius:4px;background:#0d1b2a;">` : ''}
            <span>${p.name}</span>
            ${p.price ? `<span style="margin-left:auto;color:#f0a500;font-weight:600;">$${p.price.toFixed(2)}</span>` : ''}
          </a>
        `).join('');
      } catch (e) { /* silently ignore */ }
    }, 280);
  });

  document.addEventListener('click', e => {
    if (!navInput.contains(e.target)) closeDropdown();
  });
}

// ── FLASH AUTO-DISMISS ────────────────────────────────────────────────────────
document.querySelectorAll('.flash').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity 0.4s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 400);
  }, 4000);
});

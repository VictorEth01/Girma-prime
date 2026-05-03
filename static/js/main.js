/**
 * GIRMA PRIME — main.js
 * Handles: product fetch, category filtering, cart state,
 *          sidebar open/close, checkout form, order placement.
 * No frameworks. No dependencies. Pure vanilla JS.
 */

(() => {
  'use strict';

  // ── State ──────────────────────────────────────────────────────────
  let allProducts = [];          // full product list from API
  let activeCategory = 'All';   // current filter
  const cart = loadCart();      // { productId: { product, quantity } }

  // ── DOM Refs ───────────────────────────────────────────────────────
  const productGrid    = document.getElementById('productGrid');
  const emptyState     = document.getElementById('emptyState');
  const filterButtons  = document.getElementById('filterButtons');
  const cartToggle     = document.getElementById('cartToggle');
  const cartClose      = document.getElementById('cartClose');
  const cartOverlay    = document.getElementById('cartOverlay');
  const cartSidebar    = document.getElementById('cartSidebar');
  const cartItems      = document.getElementById('cartItems');
  const cartEmpty      = document.getElementById('cartEmpty');
  const cartFooter     = document.getElementById('cartFooter');
  const cartCount      = document.getElementById('cartCount');
  const cartTotal      = document.getElementById('cartTotal');
  const checkoutBtn    = document.getElementById('checkoutBtn');
  const checkoutOverlay = document.getElementById('checkoutOverlay');
  const checkoutModal  = document.getElementById('checkoutModal');
  const checkoutClose  = document.getElementById('checkoutClose');
  const modalSummary   = document.getElementById('modalSummary');
  const placeOrderBtn  = document.getElementById('placeOrderBtn');
  const placeOrderLabel = document.getElementById('placeOrderLabel');
  const placeOrderSpinner = document.getElementById('placeOrderSpinner');
  const formError      = document.getElementById('formError');
  const formErrorText  = document.getElementById('formErrorText');
  const checkoutFormWrap = document.getElementById('checkoutFormWrap');
  const checkoutSuccess  = document.getElementById('checkoutSuccess');
  const successMessage   = document.getElementById('successMessage');
  const successClose     = document.getElementById('successClose');

  // ── Navbar scroll effect ───────────────────────────────────────────
  const navbar = document.getElementById('navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      navbar.classList.toggle('scrolled', window.scrollY > 24);
    }, { passive: true });
  }

  // ── Cart persistence ───────────────────────────────────────────────
  function loadCart() {
    try {
      return JSON.parse(localStorage.getItem('gp_cart') || '{}');
    } catch {
      return {};
    }
  }

  function saveCart() {
    localStorage.setItem('gp_cart', JSON.stringify(cart));
  }

  function clearCart() {
    Object.keys(cart).forEach(k => delete cart[k]);
    saveCart();
  }

  // ── Currency formatting ────────────────────────────────────────────
  function formatNaira(amount) {
    return '₦' + Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }

  // ── Fetch products ─────────────────────────────────────────────────
  async function fetchProducts(category = 'All') {
    const url = category === 'All'
      ? '/api/products'
      : `/api/products?category=${encodeURIComponent(category)}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
  }

  // ── Render products ────────────────────────────────────────────────
  function renderProducts(products) {
    productGrid.innerHTML = '';

    if (!products.length) {
      emptyState.classList.remove('hidden');
      return;
    }
    emptyState.classList.add('hidden');

    products.forEach((p, i) => {
      const card = document.createElement('article');
      card.className = 'product-card fade-up';
      card.style.animationDelay = `${i * 0.07}s`;
      card.dataset.productId = p.id;

      const inCart = !!cart[p.id];

      card.innerHTML = `
        <div class="product-card-img-wrap">
          <img
            src="${escapeHtml(p.image_url)}"
            alt="${escapeHtml(p.name)}"
            class="product-card-img"
            loading="lazy"
            onerror="this.src='https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=600&q=70'"
          />
          <span class="product-card-category">${escapeHtml(p.category)}</span>
        </div>
        <div class="product-card-body">
          <h3 class="product-card-name">${escapeHtml(p.name)}</h3>
          <p class="product-card-desc">${escapeHtml(p.description)}</p>
          <p class="product-card-use">Use: ${escapeHtml(p.use)}</p>
          <div class="product-card-footer">
            <span class="product-card-price">${formatNaira(p.price)}</span>
            <button
              class="add-to-cart-btn${inCart ? ' added' : ''}"
              aria-label="Add ${escapeHtml(p.name)} to cart"
              data-product-id="${p.id}"
            >
              ${inCart ? checkIcon() : plusIcon()}
            </button>
          </div>
        </div>
      `;

      productGrid.appendChild(card);
    });

    // Attach add-to-cart listeners
    productGrid.querySelectorAll('.add-to-cart-btn').forEach(btn => {
      btn.addEventListener('click', () => handleAddToCart(btn));
    });
  }

  function plusIcon() {
    return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`;
  }
  function checkIcon() {
    return `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
  }

  // ── Escape HTML to prevent XSS ─────────────────────────────────────
  function escapeHtml(str) {
    if (typeof str !== 'string') return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;');
  }

  // ── Category filter ────────────────────────────────────────────────
  filterButtons.addEventListener('click', async (e) => {
    const btn = e.target.closest('.filter-btn');
    if (!btn) return;

    const category = btn.dataset.category;
    if (category === activeCategory) return;

    activeCategory = category;

    // Update button states
    filterButtons.querySelectorAll('.filter-btn').forEach(b => {
      const isActive = b.dataset.category === category;
      b.classList.toggle('active', isActive);
      b.setAttribute('aria-selected', String(isActive));
    });

    // Show skeletons while loading
    productGrid.innerHTML = `
      <div class="skeleton rounded-2xl h-96"></div>
      <div class="skeleton rounded-2xl h-96"></div>
      <div class="skeleton rounded-2xl h-96"></div>
    `;

    try {
      const products = await fetchProducts(category);
      renderProducts(products);
    } catch (err) {
      productGrid.innerHTML = `<p class="font-sans text-sm text-moss col-span-3">Failed to load products. Please refresh.</p>`;
      console.error(err);
    }
  });

  // ── Add to cart ────────────────────────────────────────────────────
  function handleAddToCart(btn) {
    const productId = btn.dataset.productId;
    const product = allProducts.find(p => String(p.id) === String(productId));
    if (!product) return;

    if (cart[productId]) {
      // Already in cart — increment qty
      cart[productId].quantity += 1;
    } else {
      cart[productId] = { product, quantity: 1 };
      // Update button state
      btn.classList.add('added');
      btn.innerHTML = checkIcon();
    }

    saveCart();
    updateCartUI();
    bumpBadge();
  }

  // ── Cart UI ────────────────────────────────────────────────────────
  function updateCartUI() {
    const entries = Object.values(cart);

    // Count
    const totalQty = entries.reduce((s, e) => s + e.quantity, 0);
    cartCount.textContent = totalQty;
    cartCount.classList.toggle('hidden', totalQty === 0);

    // Empty vs filled
    cartEmpty.classList.toggle('hidden', entries.length > 0);
    cartFooter.classList.toggle('hidden', entries.length === 0);

    // Remove old items (keep cartEmpty sentinel)
    cartItems.querySelectorAll('.cart-item').forEach(el => el.remove());

    // Render each item
    entries.forEach(({ product, quantity }) => {
      const item = document.createElement('div');
      item.className = 'cart-item';
      item.dataset.productId = product.id;
      item.innerHTML = `
        <img src="${escapeHtml(product.image_url)}" alt="${escapeHtml(product.name)}" class="cart-item-img"
          onerror="this.src='https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=200&q=70'" />
        <div class="cart-item-info">
          <p class="cart-item-name">${escapeHtml(product.name)}</p>
          <p class="cart-item-price">${formatNaira(product.price)} each</p>
          <div class="cart-item-controls">
            <button class="qty-btn" data-action="dec" data-product-id="${product.id}" aria-label="Decrease quantity">−</button>
            <span class="qty-display">${quantity}</span>
            <button class="qty-btn" data-action="inc" data-product-id="${product.id}" aria-label="Increase quantity">+</button>
          </div>
        </div>
        <button class="cart-item-remove" data-product-id="${product.id}" aria-label="Remove ${escapeHtml(product.name)}">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      `;
      cartItems.appendChild(item);
    });

    // Total
    const total = entries.reduce((s, e) => s + (e.product.price * e.quantity), 0);
    cartTotal.textContent = formatNaira(total);

    // Qty controls
    cartItems.querySelectorAll('.qty-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.productId;
        if (btn.dataset.action === 'inc') {
          cart[id].quantity += 1;
        } else {
          cart[id].quantity -= 1;
          if (cart[id].quantity <= 0) {
            delete cart[id];
            // Revert product card button if visible
            resetProductCardBtn(id);
          }
        }
        saveCart();
        updateCartUI();
      });
    });

    // Remove buttons
    cartItems.querySelectorAll('.cart-item-remove').forEach(btn => {
      btn.addEventListener('click', () => {
        const id = btn.dataset.productId;
        delete cart[id];
        resetProductCardBtn(id);
        saveCart();
        updateCartUI();
      });
    });
  }

  function resetProductCardBtn(productId) {
    const card = productGrid.querySelector(`[data-product-id="${productId}"]`);
    if (!card) return;
    const btn = card.querySelector('.add-to-cart-btn');
    if (!btn) return;
    btn.classList.remove('added');
    btn.innerHTML = plusIcon();
  }

  function bumpBadge() {
    cartCount.classList.add('bump');
    setTimeout(() => cartCount.classList.remove('bump'), 200);
  }

  // ── Sidebar open/close ─────────────────────────────────────────────
  function openCart() {
    cartSidebar.classList.add('open');
    cartOverlay.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    cartSidebar.setAttribute('aria-hidden', 'false');
  }

  function closeCartFn() {
    cartSidebar.classList.remove('open');
    cartOverlay.classList.add('hidden');
    document.body.style.overflow = '';
    cartSidebar.setAttribute('aria-hidden', 'true');
  }

  cartToggle.addEventListener('click', openCart);
  cartClose.addEventListener('click', closeCartFn);
  cartOverlay.addEventListener('click', closeCartFn);

  // Keyboard trap in sidebar
  cartSidebar.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeCartFn();
  });

  // ── Checkout modal open/close ──────────────────────────────────────
  function openCheckout() {
    closeCartFn();

    // Reset modal state
    checkoutFormWrap.classList.remove('hidden');
    checkoutSuccess.classList.add('hidden');
    formError.classList.add('hidden');
    clearFieldErrors();

    // Build order summary
    buildModalSummary();

    // Set min datetime to now
    const dtInput = document.getElementById('deliveryDate');
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    dtInput.min = now.toISOString().slice(0, 16);

    checkoutOverlay.classList.remove('hidden');
    checkoutModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }

  function closeCheckout() {
    checkoutOverlay.classList.add('hidden');
    checkoutModal.classList.add('hidden');
    document.body.style.overflow = '';
  }

  checkoutBtn.addEventListener('click', openCheckout);
  checkoutClose.addEventListener('click', closeCheckout);
  checkoutOverlay.addEventListener('click', closeCheckout);
  successClose.addEventListener('click', () => {
    closeCheckout();
    clearCart();
    updateCartUI();
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeCheckout();
      closeCartFn();
    }
  });

  function buildModalSummary() {
    const entries = Object.values(cart);
    let html = '';
    let total = 0;

    entries.forEach(({ product, quantity }) => {
      const lineTotal = product.price * quantity;
      total += lineTotal;
      html += `
        <div class="order-summary-item">
          <span>${escapeHtml(product.name)} × ${quantity}</span>
          <span>${formatNaira(lineTotal)}</span>
        </div>
      `;
    });

    html += `
      <div class="order-summary-total">
        <span>Total</span>
        <span>${formatNaira(total)}</span>
      </div>
    `;

    modalSummary.innerHTML = html;
  }

  // ── Form validation ────────────────────────────────────────────────
  function clearFieldErrors() {
    document.querySelectorAll('.field-error').forEach(el => el.textContent = '');
    document.querySelectorAll('.field-input').forEach(el => el.classList.remove('invalid'));
  }

  function setFieldError(fieldId, message) {
    const input = document.getElementById(fieldId);
    const error = document.getElementById(`err-${fieldId}`);
    if (input) input.classList.add('invalid');
    if (error) error.textContent = message;
  }

  function validateForm() {
    clearFieldErrors();
    let valid = true;

    const name = document.getElementById('customerName').value.trim();
    const phone = document.getElementById('whatsappNumber').value.trim();
    const address = document.getElementById('deliveryAddress').value.trim();
    const date = document.getElementById('deliveryDate').value.trim();

    if (!name) {
      setFieldError('customerName', 'Please enter your full name.');
      valid = false;
    }

    const phoneDigits = phone.replace(/\D/g, '');
    if (!phone) {
      setFieldError('whatsappNumber', 'Please enter your WhatsApp number.');
      valid = false;
    } else if (phoneDigits.length < 10) {
      setFieldError('whatsappNumber', 'Enter a valid Nigerian phone number.');
      valid = false;
    }

    if (!address) {
      setFieldError('deliveryAddress', 'Please enter your delivery address.');
      valid = false;
    }

    if (!date) {
      setFieldError('deliveryDate', 'Please pick a preferred delivery date and time.');
      valid = false;
    } else {
      const chosen = new Date(date);
      if (chosen <= new Date()) {
        setFieldError('deliveryDate', 'Delivery date must be in the future.');
        valid = false;
      }
    }

    return valid;
  }

  // ── Place order ────────────────────────────────────────────────────
  placeOrderBtn.addEventListener('click', async () => {
    if (!validateForm()) return;

    const entries = Object.values(cart);
    if (!entries.length) {
      formErrorText.textContent = 'Your cart is empty.';
      formError.classList.remove('hidden');
      return;
    }

    // Build payload
    const total = entries.reduce((s, e) => s + (e.product.price * e.quantity), 0);
    const cartItemsPayload = entries.map(({ product, quantity }) => ({
      id: product.id,
      name: product.name,
      category: product.category,
      price: product.price,
      quantity
    }));

    const payload = {
      customer_name:    document.getElementById('customerName').value.trim(),
      whatsapp_number:  document.getElementById('whatsappNumber').value.trim(),
      delivery_address: document.getElementById('deliveryAddress').value.trim(),
      delivery_date:    document.getElementById('deliveryDate').value.trim(),
      cart_items:       cartItemsPayload,
      total
    };

    // Loading state
    placeOrderLabel.classList.add('hidden');
    placeOrderSpinner.classList.remove('hidden');
    placeOrderBtn.disabled = true;
    formError.classList.add('hidden');

    try {
      const res = await fetch('/api/order', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.success) {
        checkoutFormWrap.classList.add('hidden');
        checkoutSuccess.classList.remove('hidden');
        successMessage.textContent = data.message;
      } else {
        formErrorText.textContent = data.error || 'Something went wrong. Please try again.';
        formError.classList.remove('hidden');
      }
    } catch {
      formErrorText.textContent = 'Network error. Please check your connection and try again.';
      formError.classList.remove('hidden');
    } finally {
      placeOrderLabel.classList.remove('hidden');
      placeOrderSpinner.classList.add('hidden');
      placeOrderBtn.disabled = false;
    }
  });

  // ── Real-time field validation feedback ────────────────────────────
  ['customerName', 'whatsappNumber', 'deliveryAddress', 'deliveryDate'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('input', () => {
      el.classList.remove('invalid');
      const errEl = document.getElementById(`err-${id}`);
      if (errEl) errEl.textContent = '';
    });
  });

  // ── Init ───────────────────────────────────────────────────────────
  async function init() {
    try {
      allProducts = await fetchProducts('All');
      renderProducts(allProducts);
    } catch (err) {
      productGrid.innerHTML = `
        <p class="font-sans text-sm text-moss col-span-3 py-8">
          Could not load products. Please refresh the page.
        </p>
      `;
      console.error('Init failed:', err);
    }

    // Restore cart state to product buttons after render
    // (products render first, then we mark any already-carted items)
    updateCartUI();
  }

  init();

})();
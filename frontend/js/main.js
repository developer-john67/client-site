// ─── CART (local) ────────────────────────────────────────────────────────────

let cart = JSON.parse(localStorage.getItem('cart')) || [];

function updateCartCount() {
    const cartCount = document.querySelector('.cart-count');
    if (!cartCount) return;

    if (Auth.isLoggedIn()) {
        const apiCart = JSON.parse(sessionStorage.getItem('apiCart'));
        if (apiCart) {
            cartCount.textContent = apiCart.item_count || 0;
        }
    } else {
        const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
        cartCount.textContent = totalItems;
    }
}

// ─── BANNER NOTIFICATION ──────────────────────────────────────────────────────

function showBanner(message, type = 'success') {
    const existing = document.getElementById('status-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'status-banner';
    banner.textContent = message;

    const isError = type === 'error';
    Object.assign(banner.style, {
        position:      'fixed',
        top:           '0',
        left:          '0',
        width:         '100%',
        background:    isError ? '#c53030' : '#276749',
        color:         '#fff',
        padding:       '12px 16px',
        textAlign:     'center',
        fontSize:      '14px',
        fontWeight:    '500',
        letterSpacing: '0.02em',
        zIndex:        '9999',
        transform:     'translateY(-100%)',
        transition:    'transform 0.3s ease',
        boxShadow:     '0 2px 8px rgba(0,0,0,0.2)',
    });

    document.body.appendChild(banner);

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            banner.style.transform = 'translateY(0)';
        });
    });

    setTimeout(() => {
        banner.style.transform = 'translateY(-100%)';
        setTimeout(() => banner.remove(), 300);
    }, 2500);
}

// ─── PRODUCTS ─────────────────────────────────────────────────────────────────

const PLACEHOLDER_PRODUCTS = [
    { id: 1, name: 'Wireless Headphones', price: 99.99,  image_url: 'https://via.placeholder.com/300x200' },
    { id: 2, name: 'Smart Watch',         price: 199.99, image_url: 'https://via.placeholder.com/300x200' },
    { id: 3, name: 'Running Shoes',       price: 79.99,  image_url: 'https://via.placeholder.com/300x200' },
    { id: 4, name: 'Backpack',            price: 49.99,  image_url: 'https://via.placeholder.com/300x200' },
];

function buildProductCard(product) {
    return `
        <div class="product-card">
            <img
                src="${product.main_image || product.image_url || 'https://via.placeholder.com/300x200'}"
                onerror="this.src='https://via.placeholder.com/300x200'"
                alt="${product.name}"
                class="product-image"
                loading="lazy"
            >
            <div class="product-info">
                <h3 class="product-title">${product.name}</h3>
                <p class="product-price">$${parseFloat(product.price).toFixed(2)}</p>
                <button
                    class="add-to-cart"
                    onclick="addToCart('${product.product_id || product.id}', '${product.name}', ${product.price})"
                >
                    Add to Cart
                </button>
            </div>
        </div>
    `;
}

function displayFeaturedProducts() {
    const productGrid = document.getElementById('productGrid');
    if (!productGrid) return;

    Products.getAll()
        .then(data => {
            const items = data.results || data || [];
            if (items.length === 0) {
                productGrid.innerHTML = '<p class="no-products">No products available.</p>';
                return;
            }
            productGrid.innerHTML = items.map(buildProductCard).join('');
        })
        .catch(() => {
            productGrid.innerHTML = PLACEHOLDER_PRODUCTS.map(buildProductCard).join('');
        });
}

// ─── ADD TO CART ──────────────────────────────────────────────────────────────

window.addToCart = function(productId, productName, productPrice) {
    if (Auth.isLoggedIn()) {
        Cart.addItem(productId, 1)
            .then(cartData => {
                sessionStorage.setItem('apiCart', JSON.stringify(cartData));
                updateCartCount();
                showBanner(`✓ ${productName} added to cart!`);
            })
            .catch(err => showBanner(err.message || 'Failed to add to cart', 'error'));
        return;
    }

    // Guest cart (localStorage)
    const existing = cart.find(item => item.id === productId);
    if (existing) {
        existing.quantity += 1;
    } else {
        cart.push({ id: productId, name: productName, price: productPrice, quantity: 1 });
    }
    localStorage.setItem('cart', JSON.stringify(cart));
    updateCartCount();
    showBanner(`✓ ${productName} added to cart!`);
};

// ─── LOAD API CART COUNT ON PAGE LOAD ────────────────────────────────────────

async function loadApiCartCount() {
    if (!Auth.isLoggedIn()) return;
    try {
        const cartData = await Cart.get();
        sessionStorage.setItem('apiCart', JSON.stringify(cartData));
        updateCartCount();
    } catch (_) {}
}

// ─── NAV ─────────────────────────────────────────────────────────────────────

function updateNav() {
    const user       = Auth.getUser();
    const isLoggedIn = Auth.isLoggedIn();

    const btnLogin   = document.querySelector('a.btn-login');
    const btnSignup  = document.querySelector('a.btn-signup');
    const navAccount = document.querySelector('a[href="account.html"]');

    if (isLoggedIn && user) {
        if (btnLogin)   btnLogin.style.display  = 'none';
        if (btnSignup)  btnSignup.style.display = 'none';
        if (navAccount) navAccount.textContent  = user.username || 'Account';
    } else {
        if (btnLogin)   btnLogin.style.display  = '';
        if (btnSignup)  btnSignup.style.display = '';
        if (navAccount) navAccount.textContent  = 'Account';
    }
}

// ─── INIT ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    displayFeaturedProducts();
    updateNav();
    loadApiCartCount();
    updateCartCount();

    window.addEventListener('storage', (e) => {
        if (e.key === 'authToken' || e.key === 'authUser') {
            updateNav();
            loadApiCartCount();
        }
        if (e.key === 'cart') {
            cart = JSON.parse(localStorage.getItem('cart')) || [];
            updateCartCount();
        }
    });
});
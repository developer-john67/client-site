// ─── STATE ────────────────────────────────────────────────────────────────────

let userData = {
    name: 'John Doe',
    email: 'john@example.com',
    phone: '+1234567890',
    dob: '1990-01-01'
};

let addresses = [
    { id: 1, type: 'Home', street: '123 Main St',      city: 'New York', state: 'NY', zip: '10001', default: true  },
    { id: 2, type: 'Work', street: '456 Business Ave', city: 'New York', state: 'NY', zip: '10002', default: false }
];

let orders = [
    { id: 'ORD-001', date: '2024-01-15', total: 299.99, status: 'Delivered',  items: 3 },
    { id: 'ORD-002', date: '2024-02-01', total: 149.99, status: 'Shipped',    items: 2 },
    { id: 'ORD-003', date: '2024-02-10', total: 79.99,  status: 'Processing', items: 1 }
];

let paymentMethods = [
    { id: 1, type: 'visa',       last4: '4242', expiry: '12/25', default: true  },
    { id: 2, type: 'mastercard', last4: '8888', expiry: '08/26', default: false }
];

let nextAddressId = 3;
let nextPaymentId = 3;

// ─── BANNER ───────────────────────────────────────────────────────────────────

function showBanner(message, type = 'success') {
    const existing = document.getElementById('status-banner');
    if (existing) existing.remove();

    const banner = document.createElement('div');
    banner.id = 'status-banner';
    banner.textContent = message;
    Object.assign(banner.style, {
        position:      'fixed',
        top:           '0',
        left:          '0',
        width:         '100%',
        background:    type === 'error' ? '#c53030' : '#276749',
        color:         '#fff',
        padding:       '12px 16px',
        textAlign:     'center',
        fontSize:      '14px',
        fontWeight:    '500',
        zIndex:        '99999',
        transform:     'translateY(-100%)',
        transition:    'transform 0.3s ease',
        boxShadow:     '0 2px 8px rgba(0,0,0,0.2)',
    });
    document.body.appendChild(banner);
    requestAnimationFrame(() => requestAnimationFrame(() => {
        banner.style.transform = 'translateY(0)';
    }));
    setTimeout(() => {
        banner.style.transform = 'translateY(-100%)';
        setTimeout(() => banner.remove(), 300);
    }, 2500);
}

// ─── MODAL HELPERS ────────────────────────────────────────────────────────────

function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove('open');
    document.body.style.overflow = '';
}

function openConfirm(message, onConfirm) {
    const modal  = document.getElementById('confirmModal');
    const msgEl  = document.getElementById('confirmMessage');
    const yesBtn = document.getElementById('confirmYes');
    const noBtn  = document.getElementById('confirmNo');

    msgEl.textContent = message;
    openModal('confirmModal');

    const cleanup = () => {
        yesBtn.replaceWith(yesBtn.cloneNode(true));
        noBtn.replaceWith(noBtn.cloneNode(true));
    };

    document.getElementById('confirmYes').addEventListener('click', () => {
        onConfirm();
        closeModal('confirmModal');
        cleanup();
    }, { once: true });

    document.getElementById('confirmNo').addEventListener('click', () => {
        closeModal('confirmModal');
        cleanup();
    }, { once: true });
}

// Close modals when clicking the backdrop
document.addEventListener('click', e => {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal(e.target.id);
    }
});

// ─── TABS ─────────────────────────────────────────────────────────────────────

function initializeTabs() {
    document.querySelectorAll('.account-menu li').forEach(item => {
        item.addEventListener('click', () => {
            document.querySelectorAll('.account-menu li').forEach(i => i.classList.remove('active'));
            document.querySelectorAll('.account-section').forEach(s => s.classList.remove('active'));
            item.classList.add('active');
            const section = document.getElementById(item.dataset.section);
            if (section) section.classList.add('active');
        });
    });
}

// ─── PROFILE ──────────────────────────────────────────────────────────────────

function loadProfile() {
    document.getElementById('fullName').value  = userData.name;
    document.getElementById('email').value     = userData.email;
    document.getElementById('phone').value     = userData.phone;
    document.getElementById('dob').value       = userData.dob;
    document.getElementById('userName').textContent  = userData.name;
    document.getElementById('userEmail').textContent = userData.email;
}

document.addEventListener('DOMContentLoaded', () => {
    const profileForm = document.getElementById('profileForm');
    if (profileForm) {
        profileForm.addEventListener('submit', e => {
            e.preventDefault();
            userData.name  = document.getElementById('fullName').value.trim();
            userData.email = document.getElementById('email').value.trim();
            userData.phone = document.getElementById('phone').value.trim();
            userData.dob   = document.getElementById('dob').value;
            document.getElementById('userName').textContent  = userData.name;
            document.getElementById('userEmail').textContent = userData.email;
            showBanner('Profile updated successfully!');
        });
    }
});

// ─── ORDERS ───────────────────────────────────────────────────────────────────

function loadOrders() {
    const list = document.getElementById('ordersList');
    if (!list) return;

    // Try API first
    if (typeof Orders !== 'undefined') {
        Orders.getAll()
            .then(data => {
                const items = data.results || data || [];
                if (items.length === 0) { list.innerHTML = '<p class="empty-msg">No orders found.</p>'; return; }
                list.innerHTML = items.map(renderOrderCard).join('');
            })
            .catch(() => renderLocalOrders(list));
    } else {
        renderLocalOrders(list);
    }
}

function renderLocalOrders(container) {
    container.innerHTML = orders.length
        ? orders.map(renderOrderCard).join('')
        : '<p class="empty-msg">No orders found.</p>';
}

function renderOrderCard(order) {
    const statusClass = (order.status || '').toLowerCase().replace(/\s+/g, '-');
    return `
        <div class="order-card">
            <div class="order-header">
                <span class="order-id">Order #${order.id}</span>
                <span class="order-status status-${statusClass}">${order.status}</span>
            </div>
            <div class="order-details">
                <span><i class="fas fa-calendar-alt"></i> ${order.date}</span>
                <span><i class="fas fa-box"></i> ${order.items} item${order.items !== 1 ? 's' : ''}</span>
                <span><i class="fas fa-dollar-sign"></i> $${parseFloat(order.total).toFixed(2)}</span>
            </div>
        </div>`;
}

// ─── ADDRESSES ────────────────────────────────────────────────────────────────

function loadAddresses() {
    const grid = document.getElementById('addressesGrid');
    if (!grid) return;
    grid.innerHTML = addresses.length
        ? addresses.map(renderAddressCard).join('')
        : '<p class="empty-msg">No saved addresses.</p>';
}

function renderAddressCard(address) {
    return `
        <div class="address-card ${address.default ? 'default' : ''}">
            ${address.default ? '<span class="default-badge">Default</span>' : ''}
            <div class="address-type"><i class="fas fa-map-marker-alt"></i> ${address.type}</div>
            <div class="address-details">
                ${address.street}<br>
                ${address.city}, ${address.state} ${address.zip}
            </div>
            <div class="address-actions">
                ${!address.default ? `<button class="btn-ghost" onclick="setDefaultAddress(${address.id})">Set Default</button>` : ''}
                <button class="btn-ghost" onclick="editAddress(${address.id})"><i class="fas fa-edit"></i> Edit</button>
                <button class="btn-ghost btn-danger" onclick="deleteAddress(${address.id})"><i class="fas fa-trash"></i></button>
            </div>
        </div>`;
}

window.setDefaultAddress = function(id) {
    addresses.forEach(a => a.default = a.id === id);
    loadAddresses();
    showBanner('Default address updated.');
};

window.editAddress = function(id) {
    const address = addresses.find(a => a.id === id);
    if (!address) return;

    document.getElementById('addrModalTitle').textContent = 'Edit Address';
    document.getElementById('addrId').value     = address.id;
    document.getElementById('addrType').value   = address.type;
    document.getElementById('addrStreet').value = address.street;
    document.getElementById('addrCity').value   = address.city;
    document.getElementById('addrState').value  = address.state;
    document.getElementById('addrZip').value    = address.zip;
    openModal('addressModal');
};

window.deleteAddress = function(id) {
    openConfirm('Delete this address?', () => {
        addresses = addresses.filter(a => a.id !== id);
        loadAddresses();
        showBanner('Address deleted.');
    });
};

// Add / Save address modal
document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('addAddressBtn')?.addEventListener('click', () => {
        document.getElementById('addrModalTitle').textContent = 'Add New Address';
        document.getElementById('addressForm').reset();
        document.getElementById('addrId').value = '';
        openModal('addressModal');
    });

    document.getElementById('addressForm')?.addEventListener('submit', e => {
        e.preventDefault();
        const id      = document.getElementById('addrId').value;
        const payload = {
            type:   document.getElementById('addrType').value.trim()   || 'Home',
            street: document.getElementById('addrStreet').value.trim(),
            city:   document.getElementById('addrCity').value.trim(),
            state:  document.getElementById('addrState').value.trim(),
            zip:    document.getElementById('addrZip').value.trim(),
        };

        if (id) {
            const existing = addresses.find(a => a.id === parseInt(id));
            if (existing) Object.assign(existing, payload);
            showBanner('Address updated.');
        } else {
            addresses.push({ id: nextAddressId++, default: addresses.length === 0, ...payload });
            showBanner('Address added.');
        }

        closeModal('addressModal');
        loadAddresses();
    });
});

// ─── PAYMENT METHODS ─────────────────────────────────────────────────────────

function loadPaymentMethods() {
    const container = document.getElementById('paymentMethods');
    if (!container) return;
    container.innerHTML = paymentMethods.length
        ? paymentMethods.map(renderPaymentCard).join('')
        : '<p class="empty-msg">No payment methods saved.</p>';
}

function renderPaymentCard(method) {
    const icon = method.type === 'visa' ? 'fab fa-cc-visa'
               : method.type === 'mastercard' ? 'fab fa-cc-mastercard'
               : method.type === 'amex' ? 'fab fa-cc-amex'
               : 'fas fa-credit-card';
    return `
        <div class="payment-card ${method.default ? 'default' : ''}">
            ${method.default ? '<span class="default-badge">Default</span>' : ''}
            <div class="payment-info">
                <i class="${icon} payment-icon"></i>
                <div class="payment-details">
                    <h4>${method.type.charAt(0).toUpperCase() + method.type.slice(1)} •••• ${method.last4}</h4>
                    <p>Expires ${method.expiry}</p>
                </div>
            </div>
            <div class="payment-actions">
                ${!method.default ? `<button class="btn-ghost" onclick="setDefaultPayment(${method.id})">Set Default</button>` : ''}
                <button class="btn-ghost btn-danger" onclick="deletePaymentMethod(${method.id})"><i class="fas fa-trash"></i></button>
            </div>
        </div>`;
}

window.setDefaultPayment = function(id) {
    paymentMethods.forEach(m => m.default = m.id === id);
    loadPaymentMethods();
    showBanner('Default payment method updated.');
};

window.deletePaymentMethod = function(id) {
    openConfirm('Delete this payment method?', () => {
        paymentMethods = paymentMethods.filter(m => m.id !== id);
        loadPaymentMethods();
        showBanner('Payment method removed.');
    });
};

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('addPaymentBtn')?.addEventListener('click', () => {
        document.getElementById('paymentForm').reset();
        openModal('paymentModal');
    });

    document.getElementById('paymentForm')?.addEventListener('submit', e => {
        e.preventDefault();
        const raw  = document.getElementById('payCardNumber').value.replace(/\s+/g, '');
        const last4  = raw.slice(-4);
        const expiry = document.getElementById('payExpiry').value.trim();
        const type   = document.getElementById('payType').value;

        if (raw.length < 13 || raw.length > 19) {
            showBanner('Enter a valid card number.', 'error');
            return;
        }

        paymentMethods.push({ id: nextPaymentId++, type, last4, expiry, default: paymentMethods.length === 0 });
        closeModal('paymentModal');
        loadPaymentMethods();
        showBanner('Payment method added.');
    });
});

// ─── SETTINGS ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    document.getElementById('settingsForm')?.addEventListener('submit', e => {
        e.preventDefault();
        const current = document.getElementById('currentPassword').value;
        const next    = document.getElementById('newPassword').value;
        const confirm = document.getElementById('confirmPassword').value;

        if (!current) { showBanner('Enter your current password.', 'error'); return; }
        if (next.length < 6) { showBanner('New password must be at least 6 characters.', 'error'); return; }
        if (next !== confirm) { showBanner('Passwords do not match.', 'error'); return; }

        // In a real app: send to API
        e.target.reset();
        showBanner('Password updated successfully!');
    });
});

// ─── LOGOUT ──────────────────────────────────────────────────────────────────

function initLogout() {
    const btn = document.getElementById('logoutBtn');
    if (!btn) return;

    btn.addEventListener('click', async () => {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Logging out...';

        try {
            if (typeof Auth !== 'undefined') {
                await Auth.logout().catch(() => {});
            }
        } finally {
            localStorage.removeItem('authToken');
            localStorage.removeItem('authUser');
            window.location.href = 'login.html';
        }
    });
}

// ─── CART COUNT ───────────────────────────────────────────────────────────────

function updateCartCount() {
    const cart = JSON.parse(localStorage.getItem('cart')) || [];
    const cartCount = document.querySelector('.cart-count');
    if (cartCount) {
        cartCount.textContent = cart.reduce((sum, item) => sum + item.quantity, 0);
    }
}

// ─── INIT ─────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    initializeTabs();
    loadProfile();
    loadOrders();
    loadAddresses();
    loadPaymentMethods();
    updateCartCount();
    initLogout();

    // Try loading real profile from API
    if (typeof Auth !== 'undefined') {
        Auth.getProfile?.()
            .then(user => {
                if (!user) return;
                userData.name  = user.full_name || user.username || userData.name;
                userData.email = user.email || userData.email;
                loadProfile();
            })
            .catch(() => {});
    }
});
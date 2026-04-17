/**const API_BASE = 'http://localhost:8000/api';**/
const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api'
    : 'https://dropship-backend-otgc.onrender.com/api';
function getCSRFToken() {
  const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
  return cookie ? cookie.split('=')[1] : '';
}

async function request(endpoint, method = 'GET', body = null) {
  const headers = {
    'Content-Type': 'application/json',
    'X-CSRFToken': getCSRFToken(),
  };

  const token = localStorage.getItem('authToken');
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const options = { method, headers, credentials: 'include' };
  if (body) options.body = JSON.stringify(body);

  const response = await fetch(`${API_BASE}${endpoint}`, options);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    const message = error.error || error.detail || Object.values(error).flat().join(' ') || `HTTP ${response.status}`;
    throw new Error(message);
  }

  return response.status === 204 ? null : response.json();
}

function validateEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePassword(password) {
  if (!password || password.length < 8) {
    throw new Error('Password must be at least 8 characters.');
  }
}

function validateRequired(fields) {
  for (const [name, value] of Object.entries(fields)) {
    if (!value || !value.toString().trim()) {
      throw new Error(`${name} is required.`);
    }
  }
}

const Auth = {
  async login(email, password) {
    validateRequired({ 'Email': email, 'Password': password });

    if (!validateEmail(email)) {
      throw new Error('Please enter a valid email address.');
    }

    const data = await request('/users/login/', 'POST', { email, password });
    if (data.token) {
      localStorage.setItem('authToken', data.token);
      localStorage.setItem('authUser', JSON.stringify(data.user));
    }
    return data;
  },

  async logout() {
    try {
      await request('/users/logout/', 'POST');
    } catch (_) {
    } finally {
      localStorage.removeItem('authToken');
      localStorage.removeItem('authUser');
      localStorage.removeItem('cart');
      localStorage.removeItem('pendingVerificationEmail');
    }
  },

  async register(fullName, email, password, confirmPassword) {
    validateRequired({ 'Full name': fullName, 'Email': email, 'Password': password });

    if (!validateEmail(email)) {
      throw new Error('Please enter a valid email address.');
    }

    validatePassword(password);

    if (confirmPassword !== undefined && password !== confirmPassword) {
      throw new Error('Passwords do not match.');
    }

    const data = await request('/users/register/', 'POST', {
      username: fullName.trim(),
      email: email.trim(),
      password,
    });

    // Store email so the verify page can send it alongside the code
    localStorage.setItem('pendingVerificationEmail', email.trim());

    return data;
  },

  // FIX: Now sends BOTH email and code — backend requires both fields
  async verifyEmail(code) {
    if (!code || code.toString().trim().length !== 6) {
      throw new Error('Please enter a valid 6-digit code.');
    }

    const email = localStorage.getItem('pendingVerificationEmail');
    if (!email) {
      throw new Error('Session expired. Please sign up again.');
    }

    const data = await request('/users/verify-email/', 'POST', {
      email: email,
      code: code.toString().trim(),
    });

    // Clear stored email after successful verification
    localStorage.removeItem('pendingVerificationEmail');

    return data;
  },

  // Resend a new verification code — pulls email from localStorage if not passed
  async resendVerificationCode(email) {
    const targetEmail = email || localStorage.getItem('pendingVerificationEmail');
    if (!targetEmail || !validateEmail(targetEmail)) {
      throw new Error('Please provide a valid email address.');
    }
    return request('/users/resend-code/', 'POST', { email: targetEmail.trim() });
  },

  // Check if the current user's email is verified
  async checkVerificationStatus() {
    return request('/users/verification-status/');
  },

  async getProfile() {
    return request('/users/profile/');
  },

  isLoggedIn() {
    return !!localStorage.getItem('authToken');
  },

  getToken() {
    return localStorage.getItem('authToken');
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem('authUser')) || null;
    } catch {
      return null;
    }
  },
};

const Products = {
  async getAll(params = {}) {
    const query = new URLSearchParams(params).toString();
    return request(`/products/${query ? '?' + query : ''}`);
  },

  async getOne(id) {
    if (!id) throw new Error('Product ID is required.');
    return request(`/products/${id}/`);
  },

  async getByCategory(category) {
    return request(`/products/?category=${encodeURIComponent(category)}`);
  },

  async search(query) {
    if (!query || !query.trim()) throw new Error('Search query is required.');
    return request(`/products/?search=${encodeURIComponent(query)}`);
  },

  async create(formData) {
    const token = localStorage.getItem('authToken');
    if (!token) throw new Error('You must be logged in as admin.');
    const response = await fetch(`${API_BASE}/products/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-CSRFToken': getCSRFToken(),
      },
      credentials: 'include',
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed.' }));
      throw new Error(error.error || error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },

  async update(id, formData) {
    const token = localStorage.getItem('authToken');
    if (!token) throw new Error('You must be logged in as admin.');
    const response = await fetch(`${API_BASE}/products/admin/${id}/`, {
      method: 'PATCH',
      headers: {
        'Authorization': `Bearer ${token}`,
        'X-CSRFToken': getCSRFToken(),
      },
      credentials: 'include',
      body: formData,
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Update failed.' }));
      throw new Error(error.error || error.detail || `HTTP ${response.status}`);
    }
    return response.json();
  },

  async delete(id) {
    if (!id) throw new Error('Product ID is required.');
    return request(`/products/admin/${id}/`, 'DELETE');
  },
};

const Cart = {
  async get() {
    return request('/cart/');
  },

  async addItem(productId, quantity = 1) {
    if (!productId) throw new Error('Product ID is required.');
    if (quantity < 1) throw new Error('Quantity must be at least 1.');
    return request('/cart/add/', 'POST', { product_id: productId, quantity });
  },

  async updateItem(itemId, quantity) {
    if (!itemId) throw new Error('Item ID is required.');
    if (quantity < 1) throw new Error('Quantity must be at least 1.');
    return request(`/cart/items/${itemId}/`, 'PUT', { quantity });
  },

  async removeItem(itemId) {
    if (!itemId) throw new Error('Item ID is required.');
    return request(`/cart/items/${itemId}/remove/`, 'DELETE');
  },

  async clear() {
    return request('/cart/clear/', 'DELETE');
  },
};

const Orders = {
  async getAll() {
    return request('/orders/');
  },

  async getOne(id) {
    if (!id) throw new Error('Order ID is required.');
    return request(`/orders/${id}/`);
  },

  async create(orderData) {
    validateRequired({ 'Shipping address': orderData.shipping_address });
    if (!orderData.items || orderData.items.length === 0) {
      throw new Error('Order must contain at least one item.');
    }
    return request('/orders/', 'POST', orderData);
  },

  async cancel(id) {
    if (!id) throw new Error('Order ID is required.');
    return request(`/orders/${id}/cancel/`, 'POST');
  },
};
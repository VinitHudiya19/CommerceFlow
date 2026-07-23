/**
 * CommerceFlow Single Page Application Client
 * Made with pure JS and HTML, communicating with our Spring Boot API.
 */

// --- Global Application State ---
const state = {
    token: localStorage.getItem('token') || null,
    refreshToken: localStorage.getItem('refreshToken') || null,
    user: JSON.parse(localStorage.getItem('user')) || null,
    cart: { items: [], totalAmount: 0, totalItems: 0 },
    wishlist: []
};

// --- API Client Configuration ---
const API_BASE = window.location.origin; // Same host and port

/**
 * Custom fetch wrapper that adds JWT token to request headers,
 * handles token refreshes automatically, and handles global errors.
 */
async function apiCall(endpoint, options = {}) {
    // build target URL
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`;
    
    // prepare headers
    options.headers = options.headers || {};
    if (state.token) {
        options.headers['Authorization'] = `Bearer ${state.token}`;
    }
    if (!(options.body instanceof FormData) && typeof options.body === 'object') {
        options.headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.body);
    }

    try {
        let response = await fetch(url, options);
        
        // Handle unauthorized token (expired access token)
        if (response.status === 401 && state.refreshToken && !options._retry) {
            options._retry = true;
            console.log('Access token expired, attempting refresh...');
            
            const refreshed = await attemptTokenRefresh();
            if (refreshed) {
                // update authorization header and retry original call
                options.headers['Authorization'] = `Bearer ${state.token}`;
                response = await fetch(url, options);
            } else {
                logout();
                showToast('Session expired. Please log in again.', 'error');
                window.location.hash = '#/login';
                throw new Error('Unauthorized');
            }
        }

        const data = await response.json();
        
        if (!response.ok) {
            // throw backend validation messages if they exist
            throw new Error(data.message || 'Something went wrong');
        }
        
        return data; // returns the ApiResponse envelope { success, message, data }
    } catch (err) {
        console.error(`API Error on ${endpoint}:`, err);
        throw err;
    }
}

/**
 * Call refresh endpoint to get new access token using stored refresh token.
 */
async function attemptTokenRefresh() {
    try {
        const response = await fetch(`${API_BASE}/api/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refreshToken: state.refreshToken })
        });
        
        if (response.ok) {
            const res = await response.json();
            const payload = res.data;
            
            state.token = payload.accessToken;
            localStorage.setItem('token', state.token);
            console.log('Token refreshed successfully');
            return true;
        }
    } catch (e) {
        console.error('Refresh token call failed:', e);
    }
    return false;
}

// --- Auth Operations ---
function saveSession(authData) {
    state.token = authData.accessToken;
    state.refreshToken = authData.refreshToken;
    state.user = {
        email: authData.email,
        fullName: authData.fullName,
        role: authData.role
    };
    
    localStorage.setItem('token', state.token);
    localStorage.setItem('refreshToken', state.refreshToken);
    localStorage.setItem('user', JSON.stringify(state.user));
    
    updateNavbar();
    loadCart();
    loadWishlist();
}

function logout() {
    state.token = null;
    state.refreshToken = null;
    state.user = null;
    state.cart = { items: [], totalAmount: 0, totalItems: 0 };
    state.wishlist = [];
    
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
    
    updateNavbar();
    showToast('Logged out successfully', 'info');
    window.location.hash = '#/';
}

// --- Cart and Wishlist Loaders ---
async function loadCart() {
    if (!state.token) return;
    try {
        const res = await apiCall('/api/cart');
        state.cart = res.data;
        document.getElementById('cart-badge').textContent = state.cart.totalItems;
    } catch (e) {
        console.error('Failed to load cart', e);
    }
}

async function loadWishlist() {
    if (!state.token) return;
    try {
        const res = await apiCall('/api/wishlist');
        state.wishlist = res.data;
    } catch (e) {
        console.error('Failed to load wishlist', e);
    }
}

function isInWishlist(productId) {
    return state.wishlist.some(item => item.productId === productId);
}

// --- Toast Notifications ---
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'fa-check-circle';
    if (type === 'error') icon = 'fa-exclamation-circle';
    if (type === 'info') icon = 'fa-info-circle';
    
    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // remove toast after 3 seconds
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(1rem)';
        setTimeout(() => toast.remove(), 200);
    }, 3000);
}

// --- Loading indicator helper ---
function renderSpinner(containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="spinner-container">
            <div class="spinner"></div>
        </div>
    `;
}

// --- Navbar UI Sync ---
function updateNavbar() {
    const guestMenu = document.getElementById('guest-menu');
    const userMenu = document.getElementById('user-profile-menu');
    const authRequiredLinks = document.querySelectorAll('.auth-required');
    const adminOnlyLinks = document.querySelectorAll('.admin-only');

    if (state.token && state.user) {
        guestMenu.classList.add('hidden');
        userMenu.classList.remove('hidden');
        document.getElementById('nav-user-name').textContent = state.user.fullName;
        
        authRequiredLinks.forEach(link => link.classList.remove('hidden'));
        
        if (state.user.role === 'ADMIN') {
            adminOnlyLinks.forEach(link => link.classList.remove('hidden'));
        } else {
            adminOnlyLinks.forEach(link => link.classList.add('hidden'));
        }
    } else {
        guestMenu.classList.remove('hidden');
        userMenu.classList.add('hidden');
        authRequiredLinks.forEach(link => link.classList.add('hidden'));
        adminOnlyLinks.forEach(link => link.classList.add('hidden'));
        document.getElementById('cart-badge').textContent = '0';
    }
}

// --- Page Render Functions ---

/**
 * Page: Login
 */
function renderLoginPage() {
    const content = document.getElementById('app-content');
    content.innerHTML = `
        <div style="max-width: 400px; margin: 3rem auto;" class="card">
            <h2>Log In</h2>
            <p class="text-muted" style="margin-bottom: 1.5rem;">Enter your email to sign in to your account</p>
            <form id="login-form">
                <div class="form-group">
                    <label class="form-label">Email Address</label>
                    <input type="email" id="login-email" class="form-control" placeholder="name@example.com" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" id="login-password" class="form-control" placeholder="Enter password" required>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Sign In</button>
            </form>
            <p style="margin-top: 1.5rem; text-align: center; font-size: 0.9rem;">
                New to CommerceFlow? <a href="#/register" style="text-decoration: underline; font-weight: 500;">Sign Up</a>
            </p>
        </div>
    `;

    document.getElementById('login-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const email = document.getElementById('login-email').value;
        const password = document.getElementById('login-password').value;

        try {
            const res = await apiCall('/api/auth/login', {
                method: 'POST',
                body: { email, password }
            });
            saveSession(res.data);
            showToast('Login successful!');
            window.location.hash = '#/';
        } catch (err) {
            showToast(err.message, 'error');
        }
    });
}

/**
 * Page: Register
 */
function renderRegisterPage() {
    const content = document.getElementById('app-content');
    content.innerHTML = `
        <div style="max-width: 400px; margin: 2rem auto;" class="card">
            <h2>Create Account</h2>
            <p class="text-muted" style="margin-bottom: 1.5rem;">Enter details to setup a new customer account</p>
            <form id="register-form">
                <div class="form-group">
                    <label class="form-label">Full Name</label>
                    <input type="text" id="reg-name" class="form-control" placeholder="Vinit Kumar" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Email Address</label>
                    <input type="email" id="reg-email" class="form-control" placeholder="vinit@example.com" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Phone Number</label>
                    <input type="tel" id="reg-phone" class="form-control" placeholder="9876543210" required>
                </div>
                <div class="form-group">
                    <label class="form-label">Password</label>
                    <input type="password" id="reg-password" class="form-control" placeholder="Create password" required>
                </div>
                <button type="submit" class="btn btn-primary btn-block">Sign Up</button>
            </form>
            <p style="margin-top: 1.5rem; text-align: center; font-size: 0.9rem;">
                Already have an account? <a href="#/login" style="text-decoration: underline; font-weight: 500;">Log In</a>
            </p>
        </div>
    `;

    document.getElementById('register-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const fullName = document.getElementById('reg-name').value;
        const email = document.getElementById('reg-email').value;
        const phone = document.getElementById('reg-phone').value;
        const password = document.getElementById('reg-password').value;

        try {
            const res = await apiCall('/api/auth/register', {
                method: 'POST',
                body: { fullName, email, phone, password }
            });
            saveSession(res.data);
            showToast('Registration successful! Welcome.');
            window.location.hash = '#/';
        } catch (err) {
            showToast(err.message, 'error');
        }
    });
}

/**
 * Page: Products Listing (Catalog)
 */
async function renderProductsPage() {
    const content = document.getElementById('app-content');
    renderSpinner('app-content');
    
    try {
        // Fetch products and categories concurrently
        const [prodRes, catRes] = await Promise.all([
            apiCall('/api/products?size=24'),
            apiCall('/api/categories')
        ]);
        
        const products = prodRes.data.content;
        const categories = catRes.data;

        let categoryOptions = categories.map(cat => 
            `<option value="${cat.id}">${cat.name}</option>`
        ).join('');

        content.innerHTML = `
            <div class="catalog-header">
                <div>
                    <h1>Explore Products</h1>
                    <p class="text-muted">High quality minimalist items for everyday life.</p>
                </div>
            </div>

            <!-- Filters Bar -->
            <div class="card" style="margin-bottom: 2rem; padding: 1rem;">
                <div class="search-filter-bar">
                    <div class="search-input-wrap">
                        <input type="text" id="search-input" class="form-control" placeholder="Search by name...">
                    </div>
                    <div>
                        <select id="filter-category" class="form-control select-control">
                            <option value="">All Categories</option>
                            ${categoryOptions}
                        </select>
                    </div>
                    <div>
                        <select id="sort-by" class="form-control select-control">
                            <option value="createdAt,desc">Newest First</option>
                            <option value="price,asc">Price: Low to High</option>
                            <option value="price,desc">Price: High to Low</option>
                        </select>
                    </div>
                    <button id="btn-apply-filters" class="btn btn-primary">Apply</button>
                </div>
            </div>

            <!-- Products Grid -->
            <div id="products-grid" class="grid grid-cols-4">
                <!-- Renders dynamically -->
            </div>
        `;

        renderProductsList(products);

        // Bind filter event
        document.getElementById('btn-apply-filters').addEventListener('click', async () => {
            const search = document.getElementById('search-input').value;
            const categoryId = document.getElementById('filter-category').value;
            const sortVal = document.getElementById('sort-by').value.split(',');
            const sortBy = sortVal[0];
            const sortDir = sortVal[1];

            let query = `/api/products?page=0&size=24&sortBy=${sortBy}&sortDir=${sortDir}`;
            if (search) query += `&search=${encodeURIComponent(search)}`;
            if (categoryId) query += `&categoryId=${categoryId}`;

            renderSpinner('products-grid');
            try {
                const filteredRes = await apiCall(query);
                renderProductsList(filteredRes.data.content);
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

    } catch (err) {
        content.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
    }
}

function renderProductsList(products) {
    const grid = document.getElementById('products-grid');
    if (!products || products.length === 0) {
        grid.innerHTML = `<div style="grid-column: 1 / -1; padding: 3rem;" class="text-center text-muted">No products found.</div>`;
        return;
    }

    grid.innerHTML = products.map(product => {
        const imageUrl = (product.imageUrls && product.imageUrls.length > 0) 
            ? product.imageUrls[0] 
            : 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=400&q=80';
            
        const isWish = isInWishlist(product.id);
        const wishlistClass = isWish ? 'active' : '';
        const heartIcon = isWish ? 'fa-solid fa-heart' : 'fa-regular fa-heart';

        return `
            <div class="card">
                <div class="wishlist-btn-overlay ${wishlistClass}" data-id="${product.id}">
                    <i class="${heartIcon}"></i>
                </div>
                <a href="#/products/${product.id}">
                    <div class="card-image-wrap">
                        <img class="card-image" src="${imageUrl}" alt="${product.name}">
                    </div>
                    <div class="product-meta">${product.categoryName || 'General'}</div>
                    <h3>${product.name}</h3>
                    <div class="product-price">₹${Number(product.price).toFixed(2)}</div>
                </a>
                <button class="btn btn-secondary btn-block btn-add-cart" data-id="${product.id}">
                    <i class="fa-solid fa-shopping-cart"></i> Add to Cart
                </button>
            </div>
        `;
    }).join('');

    // Bind Wishlist overlays
    document.querySelectorAll('.wishlist-btn-overlay').forEach(el => {
        el.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!state.token) {
                showToast('Please login to save items', 'info');
                window.location.hash = '#/login';
                return;
            }
            const productId = parseInt(el.getAttribute('data-id'));
            const isActive = el.classList.contains('active');
            
            try {
                if (isActive) {
                    await apiCall(`/api/wishlist/${productId}`, { method: 'DELETE' });
                    el.classList.remove('active');
                    el.querySelector('i').className = 'fa-regular fa-heart';
                    showToast('Removed from wishlist');
                } else {
                    await apiCall(`/api/wishlist/${productId}`, { method: 'POST' });
                    el.classList.add('active');
                    el.querySelector('i').className = 'fa-solid fa-heart';
                    showToast('Saved to wishlist');
                }
                loadWishlist();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    });

    // Bind Cart buttons
    document.querySelectorAll('.btn-add-cart').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            if (!state.token) {
                showToast('Please login to checkout', 'info');
                window.location.hash = '#/login';
                return;
            }
            const productId = parseInt(btn.getAttribute('data-id'));
            btn.disabled = true;
            try {
                await apiCall('/api/cart/items', {
                    method: 'POST',
                    body: { productId, quantity: 1 }
                });
                showToast('Added to cart!');
                loadCart();
            } catch (err) {
                showToast(err.message, 'error');
            } finally {
                btn.disabled = false;
            }
        });
    });
}

/**
 * Page: Product Detail View
 */
async function renderProductDetailPage(id) {
    const content = document.getElementById('app-content');
    renderSpinner('app-content');

    try {
        const [prodRes, reviewsRes, ratingRes] = await Promise.all([
            apiCall(`/api/products/${id}`),
            apiCall(`/api/reviews/product/${id}`),
            apiCall(`/api/reviews/product/${id}/rating`)
        ]);

        const product = prodRes.data;
        const reviews = reviewsRes.data;
        const averageRating = ratingRes.data || 0.0;

        const imageUrl = (product.imageUrls && product.imageUrls.length > 0) 
            ? product.imageUrls[0] 
            : 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=600&q=80';

        content.innerHTML = `
            <a href="#/" class="btn btn-secondary" style="margin-bottom: 1.5rem;">
                <i class="fa-solid fa-arrow-left"></i> Back to Catalog
            </a>

            <div class="detail-layout">
                <!-- Gallery -->
                <div class="product-gallery">
                    <img src="${imageUrl}" alt="${product.name}">
                </div>

                <!-- Info panel -->
                <div>
                    <span class="product-meta">${product.categoryName || 'General'}</span>
                    <h1 style="margin-bottom: 0.5rem; font-size: 2.5rem;">${product.name}</h1>
                    
                    <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem;">
                        <div class="review-stars" style="margin-bottom: 0;">
                            ${getStarsHtml(averageRating)}
                        </div>
                        <span style="font-weight: 600;">${Number(averageRating).toFixed(1)}</span>
                        <span class="text-muted">(${reviews.length} reviews)</span>
                    </div>

                    <div class="product-price" style="font-size: 1.8rem; margin: 1.5rem 0;">₹${Number(product.price).toFixed(2)}</div>
                    
                    <p class="text-muted" style="margin-bottom: 2rem; font-size: 1rem; line-height: 1.6;">
                        ${product.description || 'No description provided for this item.'}
                    </p>
                    <div style="display: flex; gap: 1rem; max-width: 400px;">
                        <button id="detail-add-cart" class="btn btn-primary btn-block">Add to Shopping Bag</button>
                    </div>
                </div>
            </div>

            <!-- AI Highlights and Suggestions -->
            <div class="grid grid-cols-2" style="margin-top: 3rem; gap: 3rem; align-items: start;">
                <div class="card" style="padding: 1.5rem; background: #fafafa; border: 1px solid #eaeaea; border-radius: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
                        <h3 style="margin: 0; font-size: 1.2rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
                            <i class="fa-solid fa-wand-magic-sparkles" style="color: #6366f1;"></i> AI Review Summary
                        </h3>
                        <button id="btn-generate-ai-summary" class="btn btn-secondary btn-sm" style="font-size: 0.8rem; padding: 0.3rem 0.6rem; border-radius: 4px;">Generate Summary</button>
                    </div>
                    <div id="ai-summary-content" class="text-muted" style="font-size: 0.9rem; line-height: 1.6;">
                        <em>Click the button to generate an AI-powered summary of customer feedback using NLP.</em>
                    </div>
                </div>
                
                <div class="card" style="padding: 1.5rem; background: #fafafa; border: 1px solid #eaeaea; border-radius: 8px;">
                    <h3 style="margin: 0 0 1rem 0; font-size: 1.2rem; font-weight: 700; display: flex; align-items: center; gap: 0.5rem;">
                        <i class="fa-solid fa-lightbulb" style="color: #eab308;"></i> Customers Also Bought
                    </h3>
                    <div id="ai-recommendations-list" class="text-muted" style="font-size: 0.9rem; line-height: 1.6;">
                        <em>Loading suggestions...</em>
                    </div>
                </div>
            </div>

            <!-- Reviews Section -->
            <div class="reviews-section" style="margin-top: 3rem;">
                <h2>Customer Reviews</h2>
                
                <div class="grid grid-cols-2" style="align-items: start; margin-top: 1.5rem; gap: 3rem;">
                    <!-- Review List -->
                    <div>
                        ${reviews.length === 0 
                            ? '<p class="text-muted">No reviews yet. Be the first to share your thoughts!</p>' 
                            : reviews.map(r => `
                                <div class="review-card">
                                    <div class="review-stars">${getStarsHtml(r.rating)}</div>
                                    <div style="font-weight: 600; margin-bottom: 0.25rem;">${r.userName}</div>
                                    <p class="text-muted">${r.comment || 'No comment written.'}</p>
                                    <div style="font-size: 0.75rem; color: #999; margin-top: 0.4rem;">${formatDate(r.createdAt)}</div>
                                </div>
                            `).join('')
                        }
                    </div>

                    <!-- Add Review Form -->
                    <div class="card">
                        <h3>Write a Review</h3>
                        <form id="add-review-form">
                            <div class="form-group">
                                <label class="form-label">Rating</label>
                                <select id="review-rating" class="form-control select-control" required>
                                    <option value="5">5 Stars — Excellent</option>
                                    <option value="4">4 Stars — Good</option>
                                    <option value="3">3 Stars — Average</option>
                                    <option value="2">2 Stars — Poor</option>
                                    <option value="1">1 Star — Terrible</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Your Feedback</label>
                                <textarea id="review-comment" class="form-control" rows="4" placeholder="Tell other customers about your experience..." required></textarea>
                            </div>
                            <button type="submit" class="btn btn-primary btn-block">Submit Feedback</button>
                        </form>
                    </div>
                </div>
            </div>
        `;

        // Add to cart bind
        document.getElementById('detail-add-cart').addEventListener('click', async () => {
            if (!state.token) {
                showToast('Please login to add items', 'info');
                window.location.hash = '#/login';
                return;
            }
            try {
                await apiCall('/api/cart/items', {
                    method: 'POST',
                    body: { productId: id, quantity: 1 }
                });
                showToast('Added to cart!');
                loadCart();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

        // Add Review submit
        document.getElementById('add-review-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!state.token) {
                showToast('Please login to post reviews', 'info');
                window.location.hash = '#/login';
                return;
            }
            const rating = parseInt(document.getElementById('review-rating').value);
            const comment = document.getElementById('review-comment').value;

            try {
                await apiCall('/api/reviews', {
                    method: 'POST',
                    body: { productId: id, rating, comment }
                });
                showToast('Review submitted successfully!');
                renderProductDetailPage(id); // Reload view
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

        // Load AI Recommendations Async
        const recListEl = document.getElementById('ai-recommendations-list');
        if (state.token) {
            try {
                const recRes = await apiCall('/api/products/recommendations');
                const recs = recRes.data || [];
                if (recs.length === 0) {
                    recListEl.innerHTML = '<p class="text-muted" style="margin: 0;">No personalized suggestions found yet.</p>';
                } else {
                    recListEl.innerHTML = `
                        <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: 0.5rem;">
                            ${recs.map(p => `
                                <div style="display: flex; align-items: center; justify-content: space-between; padding-bottom: 0.5rem; border-bottom: 1px solid #eaeaea;">
                                    <div style="display: flex; align-items: center; gap: 0.5rem;">
                                        <img src="${p.images[0] || 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=80&q=80'}" style="width: 40px; height: 40px; border-radius: 4px; object-fit: cover;">
                                        <div>
                                            <a href="#/product/${p.id}" style="font-weight: 600; text-decoration: none; color: #111; font-size: 0.85rem;">${p.name}</a>
                                            <div style="font-size: 0.8rem; color: #999;">₹${Number(p.price).toFixed(2)}</div>
                                        </div>
                                    </div>
                                    <button class="btn btn-secondary btn-sm btn-add-rec-cart" data-id="${p.id}" style="padding: 0.25rem 0.5rem; font-size: 0.8rem; border-radius: 4px;">Add</button>
                                </div>
                            `).join('')}
                        </div>
                    `;
                    // Bind click listeners for Quick Add
                    document.querySelectorAll('.btn-add-rec-cart').forEach(btn => {
                        btn.addEventListener('click', async (e) => {
                            e.stopPropagation();
                            const pid = parseInt(btn.getAttribute('data-id'));
                            try {
                                await apiCall('/api/cart/items', {
                                    method: 'POST',
                                    body: { productId: pid, quantity: 1 }
                                });
                                showToast('Added suggestion to cart!');
                                loadCart();
                            } catch (err) {
                                showToast(err.message, 'error');
                            }
                        });
                    });
                }
            } catch (err) {
                recListEl.innerHTML = '<p class="text-muted" style="margin: 0;">Failed to load recommendations.</p>';
            }
        } else {
            recListEl.innerHTML = '<p class="text-muted" style="margin: 0;">Please login to see personalized suggestions.</p>';
        }

        // Summary generation binding
        const sumBtn = document.getElementById('btn-generate-ai-summary');
        const sumContentEl = document.getElementById('ai-summary-content');
        sumBtn.addEventListener('click', async () => {
            sumContentEl.innerHTML = '<em><i class="fa-solid fa-circle-notch fa-spin"></i> Processing feedback text...</em>';
            try {
                const sumRes = await apiCall(`/api/reviews/product/${id}/ai-summary`);
                const summaryHtml = sumRes.data.summary.split('\n').map(line => `<p style="margin-bottom: 0.5rem; margin-top: 0.5rem;">${line}</p>`).join('');
                sumContentEl.innerHTML = summaryHtml || '<em>No feedback highlights to display.</em>';
            } catch (err) {
                sumContentEl.innerHTML = `<em class="text-danger">Failed to generate summary: ${err.message}</em>`;
            }
        });

    } catch (err) {
        content.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
    }
}

function getStarsHtml(rating) {
    let stars = '';
    const rounded = Math.round(rating);
    for (let i = 1; i <= 5; i++) {
        if (i <= rounded) {
            stars += '<i class="fa-solid fa-star"></i>';
        } else {
            stars += '<i class="fa-regular fa-star"></i>';
        }
    }
    return stars;
}

/**
 * Page: Shopping Cart
 */
async function renderCartPage() {
    const content = document.getElementById('app-content');
    renderSpinner('app-content');

    try {
        const res = await apiCall('/api/cart');
        const cart = res.data;
        state.cart = cart;

        if (!cart.items || cart.items.length === 0) {
            content.innerHTML = `
                <h1>Shopping Cart</h1>
                <div class="card text-center" style="padding: 4rem 1.5rem;">
                    <i class="fa-solid fa-bag-shopping" style="font-size: 3rem; color: #ccc; margin-bottom: 1.5rem;"></i>
                    <h2>Your bag is empty</h2>
                    <p class="text-muted" style="margin-bottom: 2rem;">Items you add to your cart will appear here.</p>
                    <a href="#/" class="btn btn-primary">Start Shopping</a>
                </div>
            `;
            return;
        }

        content.innerHTML = `
            <h1>Shopping Bag</h1>
            <p class="text-muted" style="margin-bottom: 2rem;">Verify and finalize items in your shopping bag.</p>

            <div class="checkout-layout">
                <!-- Items list -->
                <div class="card" style="padding: 1.5rem 2rem;">
                    ${cart.items.map(item => `
                        <div class="cart-row" data-item-id="${item.id}">
                            <img class="cart-img" src="https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=100&q=80" alt="${item.productName}">
                            <div>
                                <h4 style="font-size: 1.05rem;">${item.productName}</h4>
                                <span class="text-muted">₹${Number(item.unitPrice).toFixed(2)}</span>
                            </div>
                            <div>
                                <div class="qty-control">
                                    <button class="btn-qty-minus" data-id="${item.id}" data-qty="${item.quantity}">-</button>
                                    <span>${item.quantity}</span>
                                    <button class="btn-qty-plus" data-id="${item.id}" data-qty="${item.quantity}">+</button>
                                </div>
                            </div>
                            <div style="font-weight: 600; text-align: right;">
                                ₹${Number(item.subtotal).toFixed(2)}
                            </div>
                            <div style="text-align: right;">
                                <button class="btn-remove-item btn-secondary btn-sm" data-id="${item.id}" style="color: var(--danger); border: none;">
                                    <i class="fa-solid fa-trash"></i>
                                </button>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <!-- Summary panel -->
                <div class="card" style="position: sticky; top: 88px;">
                    <h3>Order Summary</h3>
                    <div style="border-bottom: 1px solid var(--border-color); padding: 1.25rem 0;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.75rem;">
                            <span class="text-muted">Total Items</span>
                            <span>${cart.totalItems}</span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span class="text-muted">Delivery</span>
                            <span class="text-success" style="font-weight: 500;">FREE</span>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 1.5rem 0; font-size: 1.2rem; font-weight: 700;">
                        <span>Estimated Total</span>
                        <span>₹${Number(cart.totalAmount).toFixed(2)}</span>
                    </div>
                    <a href="#/checkout" class="btn btn-primary btn-block">Checkout Order</a>
                </div>
            </div>
        `;

        // Bind Quantities
        document.querySelectorAll('.btn-qty-minus').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.getAttribute('data-id');
                const qty = parseInt(btn.getAttribute('data-qty'));
                await updateCartItemQuantity(id, qty - 1);
            });
        });

        document.querySelectorAll('.btn-qty-plus').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.getAttribute('data-id');
                const qty = parseInt(btn.getAttribute('data-qty'));
                await updateCartItemQuantity(id, qty + 1);
            });
        });

        // Bind Removals
        document.querySelectorAll('.btn-remove-item').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = btn.getAttribute('data-id');
                try {
                    await apiCall(`/api/cart/items/${id}`, { method: 'DELETE' });
                    showToast('Item removed');
                    loadCart();
                    renderCartPage();
                } catch (e) {
                    showToast(e.message, 'error');
                }
            });
        });

    } catch (err) {
        content.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
    }
}

async function updateCartItemQuantity(itemId, quantity) {
    try {
        await apiCall(`/api/cart/items/${itemId}?quantity=${quantity}`, { method: 'PUT' });
        loadCart();
        renderCartPage();
    } catch (e) {
        showToast(e.message, 'error');
    }
}

/**
 * Page: Checkout (Select address & summary)
 */
async function renderCheckoutPage() {
    const content = document.getElementById('app-content');
    renderSpinner('app-content');

    try {
        const [cartRes, addrRes] = await Promise.all([
            apiCall('/api/cart'),
            apiCall('/api/addresses')
        ]);

        const cart = cartRes.data;
        const addresses = addrRes.data;

        if (!cart.items || cart.items.length === 0) {
            window.location.hash = '#/cart';
            return;
        }

        content.innerHTML = `
            <h1>Finalize Checkout</h1>
            <p class="text-muted" style="margin-bottom: 2.5rem;">Select delivery address and place your order.</p>

            <div class="checkout-layout">
                <!-- Address Section -->
                <div>
                    <h2>1. Delivery Address</h2>
                    <div id="address-list-container" style="margin-bottom: 1.5rem;">
                        ${addresses.length === 0 
                            ? '<p class="text-muted">No saved addresses. Please create one below.</p>' 
                            : addresses.map(addr => `
                                <div class="address-box ${addr.isDefault ? 'selected' : ''}" data-id="${addr.id}">
                                    <i class="fa-solid fa-map-marker-alt" style="margin-top: 0.2rem; color: var(--text-secondary);"></i>
                                    <div>
                                        <div style="font-weight: 600;">${addr.label}</div>
                                        <div class="text-muted">${addr.addressLine1}${addr.addressLine2 ? ', ' + addr.addressLine2 : ''}</div>
                                        <div class="text-muted">${addr.city}, ${addr.state} - ${addr.pincode}</div>
                                    </div>
                                </div>
                            `).join('')
                        }
                    </div>

                    <!-- Add Address Form Toggle -->
                    <button id="btn-toggle-address-form" class="btn btn-secondary" style="margin-bottom: 2rem;">
                        <i class="fa-solid fa-plus"></i> Add New Address
                    </button>

                    <div id="new-address-form-wrap" class="card hidden" style="margin-bottom: 2rem;">
                        <h3>Create Address</h3>
                        <form id="create-address-form" style="margin-top: 1rem;">
                            <div class="form-group">
                                <label class="form-label">Label (e.g. Home, Office)</label>
                                <input type="text" id="addr-label" class="form-control" placeholder="Home" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Address Line 1</label>
                                <input type="text" id="addr-line1" class="form-control" placeholder="House/Flat No, Block" required>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Address Line 2 (Optional)</label>
                                <input type="text" id="addr-line2" class="form-control" placeholder="Street Name, Locality">
                            </div>
                            <div class="grid grid-cols-3">
                                <div class="form-group">
                                    <label class="form-label">City</label>
                                    <input type="text" id="addr-city" class="form-control" placeholder="City" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">State</label>
                                    <input type="text" id="addr-state" class="form-control" placeholder="State" required>
                                </div>
                                <div class="form-group">
                                    <label class="form-label">Pincode</label>
                                    <input type="text" id="addr-pin" class="form-control" placeholder="110001" required>
                                </div>
                            </div>
                            <div class="form-group" style="display: flex; gap: 0.5rem; align-items: center;">
                                <input type="checkbox" id="addr-default">
                                <label for="addr-default" style="font-weight: 500; cursor: pointer;">Set as default delivery address</label>
                            </div>
                            <div style="display: flex; gap: 1rem;">
                                <button type="submit" class="btn btn-primary">Save Address</button>
                                <button type="button" id="btn-cancel-address" class="btn btn-secondary">Cancel</button>
                            </div>
                        </form>
                    </div>
                </div>

                <!-- Summary & Place Order -->
                <div class="card" style="position: sticky; top: 88px;">
                    <h2>2. Checkout Summary</h2>
                    <div style="margin: 1.5rem 0; border-bottom: 1px solid var(--border-color); padding-bottom: 1rem;">
                        ${cart.items.map(item => `
                            <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 0.5rem;">
                                <span class="text-muted">${item.productName} (x${item.quantity})</span>
                                <span>₹${Number(item.subtotal).toFixed(2)}</span>
                            </div>
                        `).join('')}
                    </div>
                    <div style="display: flex; justify-content: space-between; padding: 0.5rem 0; font-size: 1.15rem; font-weight: 700; margin-bottom: 1.5rem;">
                        <span>Order Total</span>
                        <span>₹${Number(cart.totalAmount).toFixed(2)}</span>
                    </div>

                    <button id="btn-place-order" class="btn btn-primary btn-block">Place Order & Pay</button>
                </div>
            </div>
        `;

        // Bind address selection
        let selectedAddressId = null;
        const defaultBox = document.querySelector('.address-box.selected');
        if (defaultBox) {
            selectedAddressId = parseInt(defaultBox.getAttribute('data-id'));
        }

        document.querySelectorAll('.address-box').forEach(box => {
            box.addEventListener('click', () => {
                document.querySelectorAll('.address-box').forEach(b => b.classList.remove('selected'));
                box.classList.add('selected');
                selectedAddressId = parseInt(box.getAttribute('data-id'));
            });
        });

        // Toggle address form
        const toggleBtn = document.getElementById('btn-toggle-address-form');
        const formWrap = document.getElementById('new-address-form-wrap');
        const cancelBtn = document.getElementById('btn-cancel-address');

        toggleBtn.addEventListener('click', () => {
            formWrap.classList.remove('hidden');
            toggleBtn.classList.add('hidden');
        });

        cancelBtn.addEventListener('click', () => {
            formWrap.classList.add('hidden');
            toggleBtn.classList.remove('hidden');
        });

        // Submit address form
        document.getElementById('create-address-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const label = document.getElementById('addr-label').value;
            const addressLine1 = document.getElementById('addr-line1').value;
            const addressLine2 = document.getElementById('addr-line2').value;
            const city = document.getElementById('addr-city').value;
            const state = document.getElementById('addr-state').value;
            const pincode = document.getElementById('addr-pin').value;
            const isDefault = document.getElementById('addr-default').checked;

            try {
                await apiCall('/api/addresses', {
                    method: 'POST',
                    body: { label, addressLine1, addressLine2, city, state, pincode, isDefault }
                });
                showToast('Address saved successfully!');
                renderCheckoutPage(); // Reload
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

        // Place Order button
        document.getElementById('btn-place-order').addEventListener('click', async () => {
            if (!selectedAddressId) {
                showToast('Please select or add a delivery address', 'error');
                return;
            }

            try {
                const res = await apiCall('/api/orders', {
                    method: 'POST',
                    body: { addressId: selectedAddressId }
                });
                
                const placedOrder = res.data;
                showToast('Order placed successfully!');
                loadCart(); // Refresh badges

                // Open payment mock automatically
                initiateMockPayment(placedOrder.id);
            } catch (err) {
                showToast(err.message, 'error');
            }
        });

    } catch (err) {
        content.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
    }
}

/**
 * Initiates the Payment Modal flow using backend payment details
 */
async function initiateMockPayment(orderId) {
    try {
        // Fetch payment initiated details for order
        const payRes = await apiCall(`/api/payments/order/${orderId}`);
        const payment = payRes.data;

        // Populate Modal Fields
        document.getElementById('pay-order-id').textContent = `#${payment.orderId}`;
        document.getElementById('pay-amount').textContent = `₹${Number(payment.amount).toFixed(2)}`;
        document.getElementById('pay-txn-id').textContent = payment.transactionId;
        
        const modal = document.getElementById('payment-modal');
        modal.classList.remove('hidden');

        // Clean event listeners to avoid duplicates
        const approveBtn = document.getElementById('btn-approve-payment');
        const cancelBtn = document.getElementById('btn-cancel-payment');
        const closeBtn = document.getElementById('btn-close-payment');

        const closeFunc = () => {
            modal.classList.add('hidden');
            window.location.hash = '#/orders'; // Redirect to orders history
        };

        closeBtn.onclick = closeFunc;
        cancelBtn.onclick = closeFunc;

        approveBtn.onclick = async () => {
            approveBtn.disabled = true;
            try {
                await apiCall(`/api/payments/${payment.id}/verify`, { method: 'POST' });
                showToast('Payment verified successfully!');
                modal.classList.add('hidden');
                window.location.hash = '#/orders';
            } catch (err) {
                showToast(err.message, 'error');
            } finally {
                approveBtn.disabled = false;
            }
        };

    } catch (e) {
        showToast('Failed to load payment details', 'error');
        window.location.hash = '#/orders';
    }
}

/**
 * Page: User Orders History
 */
async function renderOrdersPage() {
    const content = document.getElementById('app-content');
    renderSpinner('app-content');

    try {
        const res = await apiCall('/api/orders');
        const orders = res.data;

        if (!orders || orders.length === 0) {
            content.innerHTML = `
                <h1>Order History</h1>
                <div class="card text-center" style="padding: 4rem 1.5rem;">
                    <i class="fa-solid fa-receipt" style="font-size: 3rem; color: #ccc; margin-bottom: 1.5rem;"></i>
                    <h2>No orders placed yet</h2>
                    <p class="text-muted" style="margin-bottom: 2rem;">Purchases you make will show up here.</p>
                    <a href="#/" class="btn btn-primary">Catalog</a>
                </div>
            `;
            return;
        }

        content.innerHTML = `
            <h1>Your Orders</h1>
            <p class="text-muted" style="margin-bottom: 2.5rem;">Track and review your purchases.</p>

            <div class="grid grid-cols-1" style="gap: 1.5rem;">
                ${orders.map(order => {
                    const statusClass = `status-tag-${order.status.toLowerCase()}`;
                    const showPayBtn = order.status === 'PLACED';
                    const showCancelBtn = order.status === 'PLACED' || order.status === 'CONFIRMED';
                    
                    return `
                        <div class="card">
                            <div class="card-header-flex">
                                <div>
                                    <h3 style="margin-bottom: 0.25rem;">Order #${order.id}</h3>
                                    <span class="text-muted" style="font-size: 0.85rem;">Date: ${formatDate(order.createdAt)}</span>
                                </div>
                                <span class="status-tag ${statusClass}">${order.status}</span>
                            </div>
                            
                            <!-- Items -->
                            <div style="border-top: 1px solid var(--border-color); border-bottom: 1px solid var(--border-color); padding: 1rem 0; margin-bottom: 1.25rem;">
                                ${order.items.map(item => `
                                    <div style="display: flex; justify-content: space-between; font-size: 0.9rem; margin-bottom: 0.5rem;">
                                        <span>${item.productName} <strong>(x${item.quantity})</strong></span>
                                        <span class="text-muted">₹${Number(item.subtotal).toFixed(2)}</span>
                                    </div>
                                `).join('')}
                            </div>
                            
                            <!-- Summary Row -->
                            <div class="card-header-flex" style="align-items: center; margin-bottom: 0;">
                                <div>
                                    <span class="text-muted" style="font-size: 0.85rem;">Deliver to:</span>
                                    <div style="font-size: 0.9rem; font-weight: 500; color: var(--text-secondary);">${order.deliveryAddress}</div>
                                </div>
                                <div style="text-align: right;">
                                    <div style="font-size: 0.85rem; color: var(--text-secondary);">Total Paid</div>
                                    <strong style="font-size: 1.3rem;">₹${Number(order.totalAmount).toFixed(2)}</strong>
                                </div>
                            </div>
                            
                            <!-- Actions -->
                            <div style="margin-top: 1.25rem; display: flex; gap: 0.75rem; justify-content: flex-end;">
                                ${showPayBtn ? `<button class="btn btn-primary btn-sm btn-pay-order" data-id="${order.id}">Complete Payment</button>` : ''}
                                ${showCancelBtn ? `<button class="btn btn-secondary btn-sm btn-cancel-order" data-id="${order.id}" style="color: var(--danger);">Cancel Order</button>` : ''}
                            </div>
                        </div>
                    `;
                }).join('')}
            </div>
        `;

        // Bind Pay Order
        document.querySelectorAll('.btn-pay-order').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-id');
                initiateMockPayment(id);
            });
        });

        // Bind Cancel Order
        document.querySelectorAll('.btn-cancel-order').forEach(btn => {
            btn.addEventListener('click', async () => {
                if (confirm('Are you sure you want to cancel this order?')) {
                    const id = btn.getAttribute('data-id');
                    try {
                        await apiCall(`/api/orders/${id}/cancel`, { method: 'PATCH' });
                        showToast('Order cancelled successfully.');
                        renderOrdersPage();
                    } catch (e) {
                        showToast(e.message, 'error');
                    }
                }
            });
        });

    } catch (err) {
        content.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
    }
}

/**
 * Page: Wishlist Listing
 */
async function renderWishlistPage() {
    const content = document.getElementById('app-content');
    renderSpinner('app-content');

    try {
        const res = await apiCall('/api/wishlist');
        const items = res.data;
        state.wishlist = items;

        if (!items || items.length === 0) {
            content.innerHTML = `
                <h1>Your Wishlist</h1>
                <div class="card text-center" style="padding: 4rem 1.5rem;">
                    <i class="fa-solid fa-heart" style="font-size: 3rem; color: #ccc; margin-bottom: 1.5rem;"></i>
                    <h2>Wishlist is empty</h2>
                    <p class="text-muted" style="margin-bottom: 2rem;">Save products here to buy them later.</p>
                    <a href="#/" class="btn btn-primary">Start Browsing</a>
                </div>
            `;
            return;
        }

        content.innerHTML = `
            <h1>Saved Items</h1>
            <p class="text-muted" style="margin-bottom: 2.5rem;">Your personal curated catalog.</p>

            <div class="table-responsive">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Product Details</th>
                            <th>Date Added</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${items.map(item => `
                            <tr>
                                <td>
                                    <a href="#/products/${item.productId}" style="font-weight: 600; text-decoration: underline;">
                                        ${item.productName}
                                    </a>
                                </td>
                                <td class="text-muted">${formatDate(item.addedAt)}</td>
                                <td>
                                    <button class="btn btn-primary btn-sm btn-wishlist-cart" data-id="${item.productId}">
                                        Add to Cart
                                    </button>
                                    <button class="btn btn-secondary btn-sm btn-wishlist-remove" data-id="${item.productId}" style="color: var(--danger);">
                                        Remove
                                    </button>
                                </td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        `;

        // Bind Wishlist Cart button
        document.querySelectorAll('.btn-wishlist-cart').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = parseInt(btn.getAttribute('data-id'));
                try {
                    await apiCall('/api/cart/items', {
                        method: 'POST',
                        body: { productId: id, quantity: 1 }
                    });
                    showToast('Added to cart!');
                    loadCart();
                } catch (e) {
                    showToast(e.message, 'error');
                }
            });
        });

        // Bind Wishlist Remove button
        document.querySelectorAll('.btn-wishlist-remove').forEach(btn => {
            btn.addEventListener('click', async () => {
                const id = parseInt(btn.getAttribute('data-id'));
                try {
                    await apiCall(`/api/wishlist/${id}`, { method: 'DELETE' });
                    showToast('Removed from wishlist');
                    loadWishlist();
                    renderWishlistPage(); // Reload
                } catch (e) {
                    showToast(e.message, 'error');
                }
            });
        });

    } catch (err) {
        content.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
    }
}

/**
 * Page: Admin Dashboard & Control
 */
async function renderAdminPage() {
    if (!state.token || state.user.role !== 'ADMIN') {
        window.location.hash = '#/';
        return;
    }

    const content = document.getElementById('app-content');
    renderSpinner('app-content');

    try {
        const [statsRes, productsRes, inventoryRes, categoriesRes] = await Promise.all([
            apiCall('/api/admin/dashboard'),
            apiCall('/api/products?size=100'),
            apiCall('/api/inventory'),
            apiCall('/api/categories')
        ]);

        const stats = statsRes.data;
        const products = productsRes.data.content;
        const inventory = inventoryRes.data;
        const categories = categoriesRes.data;

        content.innerHTML = `
            <h1>Admin Control Panel</h1>
            <p class="text-muted" style="margin-bottom: 2rem;">Manage catalog and view dashboard statistics.</p>

            <!-- Dashboard Stats -->
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Revenue</div>
                    <div class="stat-value">₹${Number(stats.totalRevenue).toFixed(2)}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Users</div>
                    <div class="stat-value">${stats.totalUsers}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Total Orders</div>
                    <div class="stat-value">${stats.totalOrders}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Pending Orders</div>
                    <div class="stat-value" style="color: var(--warning);">${stats.pendingOrders}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Low Stock items</div>
                    <div class="stat-value" style="color: var(--danger);">${stats.lowStockProducts}</div>
                </div>
            </div>

            <!-- Tab Headers -->
            <div class="tabs-header">
                <button class="tab-btn active" id="tab-products">Manage Products</button>
                <button class="tab-btn" id="tab-inventory">Manage Stock</button>
            </div>

            <!-- Tab Contents -->
            <div id="admin-tab-content">
                <!-- Loaded Dynamically -->
            </div>
        `;

        const renderTabProducts = () => {
            const wrap = document.getElementById('admin-tab-content');
            wrap.innerHTML = `
                <div class="grid grid-cols-3" style="align-items: start; gap: 2rem;">
                    <!-- Create Form -->
                    <div class="card" style="grid-column: 1 / 2;">
                        <h3>Add New Product</h3>
                        <form id="admin-create-product-form" style="margin-top: 1rem;">
                            <div class="form-group">
                                <label class="form-label">Product Name</label>
                                <input type="text" id="admin-prod-name" class="form-control" required placeholder="e.g. Leather Shoes">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Description</label>
                                <textarea id="admin-prod-desc" class="form-control" rows="3" placeholder="Description details..." required></textarea>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Price (INR)</label>
                                <input type="number" step="0.01" id="admin-prod-price" class="form-control" required placeholder="999.00">
                            </div>
                            <div class="form-group">
                                <label class="form-label">Category</label>
                                <select id="admin-prod-cat" class="form-control select-control" required>
                                    ${categories.map(c => `<option value="${c.id}">${c.name}</option>`).join('')}
                                </select>
                            </div>
                            <div class="form-group">
                                <label class="form-label">Image URL</label>
                                <input type="text" id="admin-prod-img" class="form-control" placeholder="https://unsplash.com/...">
                            </div>
                            <button type="submit" class="btn btn-primary btn-block">Publish Product</button>
                        </form>
                    </div>

                    <!-- Product Table -->
                    <div class="table-responsive" style="grid-column: 2 / 4;">
                        <h3>Current Catalog (${products.length})</h3>
                        <table class="table" style="margin-top: 1rem;">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Category</th>
                                    <th>Price</th>
                                    <th>Status</th>
                                    <th>Action</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${products.map(p => `
                                    <tr>
                                        <td><strong>${p.name}</strong></td>
                                        <td class="text-muted">${p.categoryName || '-'}</td>
                                        <td>₹${Number(p.price).toFixed(2)}</td>
                                        <td>
                                            <span class="status-tag ${p.active ? 'status-tag-delivered' : 'status-tag-cancelled'}">
                                                ${p.active ? 'ACTIVE' : 'INACTIVE'}
                                            </span>
                                        </td>
                                        <td>
                                            ${p.active 
                                                ? `<button class="btn btn-danger btn-sm btn-deactivate-prod" data-id="${p.id}">Deactivate</button>` 
                                                : '<span class="text-muted">-</span>'
                                            }
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            `;

            // Bind create
            document.getElementById('admin-create-product-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const name = document.getElementById('admin-prod-name').value;
                const description = document.getElementById('admin-prod-desc').value;
                const price = parseFloat(document.getElementById('admin-prod-price').value);
                const categoryId = parseInt(document.getElementById('admin-prod-cat').value);
                const img = document.getElementById('admin-prod-img').value;
                const imageUrls = img ? [img] : [];

                try {
                    await apiCall('/api/products', {
                        method: 'POST',
                        body: { name, description, price, categoryId, imageUrls }
                    });
                    showToast('Product published successfully!');
                    renderAdminPage();
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });

            // Bind deactivations
            document.querySelectorAll('.btn-deactivate-prod').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const id = btn.getAttribute('data-id');
                    if (confirm('Deactivate this product? This hides it from catalog.')) {
                        try {
                            await apiCall(`/api/products/${id}`, { method: 'DELETE' });
                            showToast('Product deactivated');
                            renderAdminPage();
                        } catch (err) {
                            showToast(err.message, 'error');
                        }
                    }
                });
            });
        };

        const renderTabInventory = () => {
            const wrap = document.getElementById('admin-tab-content');
            wrap.innerHTML = `
                <div class="table-responsive">
                    <h3>Stock & Threshold Configurations</h3>
                    <table class="table" style="margin-top: 1rem;">
                        <thead>
                            <tr>
                                <th>Product ID</th>
                                <th>Product Name</th>
                                <th>Quantity</th>
                                <th>Low Stock Threshold</th>
                                <th>Stock Status</th>
                                <th>Update Stock</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${products.map(p => {
                                const stockItem = inventory.find(inv => inv.productId === p.id) || { quantity: 0, lowStockThreshold: 10, lowStock: true, outOfStock: true };
                                const statusText = stockItem.outOfStock 
                                    ? 'OUT OF STOCK' 
                                    : (stockItem.lowStock ? 'LOW STOCK' : 'IN STOCK');
                                    
                                const statusClass = stockItem.outOfStock 
                                    ? 'status-tag-cancelled' 
                                    : (stockItem.lowStock ? 'status-tag-placed' : 'status-tag-delivered');

                                return `
                                    <tr>
                                        <td>#${p.id}</td>
                                        <td><strong>${p.name}</strong></td>
                                        <td>${stockItem.quantity} units</td>
                                        <td>${stockItem.lowStockThreshold} units</td>
                                        <td>
                                            <span class="status-tag ${statusClass}">${statusText}</span>
                                        </td>
                                        <td>
                                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                                <input type="number" class="form-control admin-qty-input" data-id="${p.id}" value="${stockItem.quantity}" style="width: 80px; padding: 0.25rem;">
                                                <button class="btn btn-secondary btn-sm btn-update-stock" data-id="${p.id}">Save</button>
                                            </div>
                                        </td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>
            `;

            // Bind updates
            document.querySelectorAll('.btn-update-stock').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const id = btn.getAttribute('data-id');
                    const input = document.querySelector(`.admin-qty-input[data-id="${id}"]`);
                    const quantity = parseInt(input.value);

                    try {
                        await apiCall(`/api/inventory/product/${id}?quantity=${quantity}`, { method: 'PUT' });
                        showToast('Stock count saved');
                        renderAdminPage();
                    } catch (e) {
                        showToast(e.message, 'error');
                    }
                });
            });
        };

        // Bind Tabs toggles
        const btnProd = document.getElementById('tab-products');
        const btnInv = document.getElementById('tab-inventory');

        btnProd.addEventListener('click', () => {
            btnProd.classList.add('active');
            btnInv.classList.remove('active');
            renderTabProducts();
        });

        btnInv.addEventListener('click', () => {
            btnInv.classList.add('active');
            btnProd.classList.remove('active');
            renderTabInventory();
        });

        // Load default tab
        renderTabProducts();

    } catch (e) {
        content.innerHTML = `<div class="alert alert-danger">${e.message}</div>`;
    }
}

// --- Date Helper ---
function formatDate(dateTimeStr) {
    if (!dateTimeStr) return '-';
    const date = new Date(dateTimeStr);
    return date.toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// --- Client-Side Router ---
const routes = {
    '/': renderProductsPage,
    '/login': renderLoginPage,
    '/register': renderRegisterPage,
    '/cart': renderCartPage,
    '/checkout': renderCheckoutPage,
    '/orders': renderOrdersPage,
    '/wishlist': renderWishlistPage,
    '/admin': renderAdminPage
};

function router() {
    const hash = window.location.hash || '#/';
    
    // Exact routes
    let pageFunc = routes[hash.substring(1)];
    
    // Dynamic routes (like #/products/1)
    if (!pageFunc) {
        const prodMatch = hash.match(/^#\/products\/(\d+)$/);
        if (prodMatch) {
            const id = parseInt(prodMatch[1]);
            pageFunc = () => renderProductDetailPage(id);
        }
    }
    
    // Fallback to Catalog (products) page
    if (!pageFunc) {
        pageFunc = renderProductsPage;
    }

    // Update active nav links style
    document.querySelectorAll('.nav-link').forEach(link => link.classList.remove('active'));
    if (hash === '#/') document.getElementById('nav-products')?.classList.add('active');
    if (hash === '#/wishlist') document.getElementById('nav-wishlist')?.classList.add('active');
    if (hash === '#/cart') document.getElementById('nav-cart')?.classList.add('active');
    if (hash === '#/orders') document.getElementById('nav-orders')?.classList.add('active');
    if (hash === '#/admin') document.getElementById('nav-admin')?.classList.add('active');

    pageFunc();
}

// --- Application Init ---
window.addEventListener('DOMContentLoaded', () => {
    updateNavbar();
    loadCart();
    loadWishlist();
    
    window.addEventListener('hashchange', router);
    router(); // First load router check

    // Global Logout Bind
    document.getElementById('btn-logout').addEventListener('click', logout);
});

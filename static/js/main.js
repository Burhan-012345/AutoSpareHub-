/**
 * AutoSpareHub Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initPasswordToggle();
    initCartActions();
    initProductFilters();
    initVehicleSearch();
    initQuantityControls();
    initFormValidation();
    initMobileMenu();
    initScrollToTop();
    initLazyLoading();
    initNotifications();
});

/**
 * Password toggle visibility
 */
function initPasswordToggle() {
    document.querySelectorAll('.password-toggle').forEach(toggle => {
        toggle.addEventListener('click', function() {
            const input = this.closest('.input-group').querySelector('input');
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.remove('fa-eye');
                icon.classList.add('fa-eye-slash');
                this.setAttribute('aria-label', 'Hide password');
            } else {
                input.type = 'password';
                icon.classList.remove('fa-eye-slash');
                icon.classList.add('fa-eye');
                this.setAttribute('aria-label', 'Show password');
            }
        });
    });
}

/**
 * Initialize cart actions
 */
function initCartActions() {
    // Add to cart buttons
    document.querySelectorAll('.add-to-cart').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            
            const productId = this.dataset.productId;
            const quantity = this.closest('.product-actions')?.querySelector('.quantity-input')?.value || 1;
            
            // Show loading state
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Adding...';
            this.disabled = true;
            
            try {
                const response = await fetch('/cart/add/' + productId, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: `quantity=${quantity}`
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Update cart count
                    updateCartCount(data.cart_count);
                    
                    // Show success animation
                    this.classList.add('cart-add-animation');
                    showNotification(data.message, 'success');
                    
                    // Reset button after animation
                    setTimeout(() => {
                        this.innerHTML = originalText;
                        this.disabled = false;
                        this.classList.remove('cart-add-animation');
                    }, 500);
                } else {
                    showNotification(data.message, 'error');
                    this.innerHTML = originalText;
                    this.disabled = false;
                }
            } catch (error) {
                console.error('Error adding to cart:', error);
                showNotification('Failed to add to cart. Please try again.', 'error');
                this.innerHTML = originalText;
                this.disabled = false;
            }
        });
    });
    
    // Update cart quantity
    document.querySelectorAll('.update-quantity').forEach(button => {
        button.addEventListener('click', async function() {
            const input = this.closest('.quantity-control').querySelector('.quantity-input');
            const itemId = this.closest('.cart-item').dataset.itemId;
            const newQuantity = parseInt(input.value);
            
            if (newQuantity < 1) {
                showNotification('Quantity must be at least 1', 'warning');
                return;
            }
            
            try {
                const response = await fetch('/cart/update/' + itemId, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: `quantity=${newQuantity}`
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Update item total
                    const itemTotal = this.closest('.cart-item').querySelector('.item-total');
                    if (itemTotal) {
                        itemTotal.textContent = `₹${data.item_total.toFixed(2)}`;
                    }
                    
                    // Update cart totals
                    updateCartTotals();
                    showNotification('Cart updated', 'success');
                } else {
                    showNotification(data.message, 'error');
                }
            } catch (error) {
                console.error('Error updating cart:', error);
                showNotification('Failed to update cart', 'error');
            }
        });
    });
    
    // Remove from cart
    document.querySelectorAll('.remove-from-cart').forEach(button => {
        button.addEventListener('click', async function() {
            if (!confirm('Are you sure you want to remove this item from your cart?')) {
                return;
            }
            
            const itemId = this.dataset.itemId;
            const cartItem = this.closest('.cart-item');
            
            try {
                const response = await fetch('/cart/remove/' + itemId, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Remove item from DOM with animation
                    cartItem.style.opacity = '0';
                    cartItem.style.transform = 'translateX(-100%)';
                    
                    setTimeout(() => {
                        cartItem.remove();
                        updateCartCount(data.cart_count);
                        updateCartTotals();
                        
                        // Check if cart is empty
                        if (data.cart_count === 0) {
                            document.querySelector('.cart-items').innerHTML = `
                                <div class="text-center py-5">
                                    <i class="fas fa-shopping-cart fa-4x text-muted mb-3"></i>
                                    <h4 class="text-muted">Your cart is empty</h4>
                                    <p class="text-muted">Add some products to get started!</p>
                                    <a href="/shop" class="btn btn-primary mt-3">
                                        <i class="fas fa-shopping-bag me-2"></i>Continue Shopping
                                    </a>
                                </div>
                            `;
                        }
                    }, 300);
                    
                    showNotification(data.message, 'success');
                } else {
                    showNotification(data.message, 'error');
                }
            } catch (error) {
                console.error('Error removing from cart:', error);
                showNotification('Failed to remove item', 'error');
            }
        });
    });
}

/**
 * Update cart count in navbar
 */
function updateCartCount(count) {
    const cartBadge = document.querySelector('.cart-count');
    const cartLink = document.querySelector('.cart-badge');
    
    if (count > 0) {
        if (cartBadge) {
            cartBadge.textContent = count;
        } else if (cartLink) {
            const badge = document.createElement('span');
            badge.className = 'cart-count';
            badge.textContent = count;
            cartLink.appendChild(badge);
        }
    } else if (cartBadge) {
        cartBadge.remove();
    }
}

/**
 * Update cart totals
 */
async function updateCartTotals() {
    try {
        const response = await fetch('/api/cart/total');
        const data = await response.json();
        
        // Update totals in cart page
        document.querySelectorAll('.cart-subtotal').forEach(el => {
            el.textContent = `₹${data.subtotal.toFixed(2)}`;
        });
        
        document.querySelectorAll('.cart-tax').forEach(el => {
            el.textContent = `₹${data.tax.toFixed(2)}`;
        });
        
        document.querySelectorAll('.cart-shipping').forEach(el => {
            el.textContent = `₹${data.shipping.toFixed(2)}`;
        });
        
        document.querySelectorAll('.cart-total').forEach(el => {
            el.textContent = `₹${data.total.toFixed(2)}`;
        });
    } catch (error) {
        console.error('Error updating cart totals:', error);
    }
}

/**
 * Initialize product filters
 */
function initProductFilters() {
    const filterForm = document.getElementById('product-filters');
    if (!filterForm) return;
    
    // Range sliders for price
    const priceRange = document.getElementById('price-range');
    const priceValue = document.getElementById('price-value');
    
    if (priceRange && priceValue) {
        priceRange.addEventListener('input', function() {
            priceValue.textContent = `₹${this.value}`;
        });
    }
    
    // Category filter
    document.querySelectorAll('.category-filter').forEach(filter => {
        filter.addEventListener('change', function() {
            filterForm.submit();
        });
    });
    
    // Apply filters button
    const applyFilters = document.getElementById('apply-filters');
    if (applyFilters) {
        applyFilters.addEventListener('click', function() {
            filterForm.submit();
        });
    }
    
    // Clear filters button
    const clearFilters = document.getElementById('clear-filters');
    if (clearFilters) {
        clearFilters.addEventListener('click', function() {
            const inputs = filterForm.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (input.type === 'checkbox' || input.type === 'radio') {
                    input.checked = false;
                } else if (input.type === 'text' || input.type === 'number') {
                    input.value = '';
                } else if (input.tagName === 'SELECT') {
                    input.selectedIndex = 0;
                }
            });
            filterForm.submit();
        });
    }
}

/**
 * Initialize vehicle-based search
 */
function initVehicleSearch() {
    const brandSelect = document.getElementById('vehicle-brand');
    const modelSelect = document.getElementById('vehicle-model');
    const yearSelect = document.getElementById('vehicle-year');
    const searchBtn = document.getElementById('vehicle-search-btn');
    
    if (!brandSelect) return;
    
    // Load models when brand changes
    brandSelect.addEventListener('change', async function() {
        const brandId = this.value;
        
        if (!brandId) {
            modelSelect.innerHTML = '<option value="">Select Model</option>';
            modelSelect.disabled = true;
            return;
        }
        
        try {
            const response = await fetch(`/api/models/${brandId}`);
            const models = await response.json();
            
            modelSelect.innerHTML = '<option value="">Select Model</option>';
            models.forEach(model => {
                const option = document.createElement('option');
                option.value = model.id;
                option.textContent = model.name;
                modelSelect.appendChild(option);
            });
            
            modelSelect.disabled = false;
            
            // Clear year selection
            yearSelect.innerHTML = '<option value="">Select Year</option>';
            yearSelect.disabled = true;
        } catch (error) {
            console.error('Error loading models:', error);
        }
    });
    
    // Load years when model changes
    if (modelSelect) {
        modelSelect.addEventListener('change', async function() {
            const modelId = this.value;
            const brandId = brandSelect.value;
            
            if (!modelId) {
                yearSelect.innerHTML = '<option value="">Select Year</option>';
                yearSelect.disabled = true;
                return;
            }
            
            try {
                // Get years for this brand/model combination
                const response = await fetch(`/api/products/by-vehicle?brand_id=${brandId}&model_id=${modelId}`);
                const products = await response.json();
                
                // Extract unique years
                const years = [...new Set(products.map(p => p.year))].filter(Boolean).sort();
                
                yearSelect.innerHTML = '<option value="">Select Year</option>';
                years.forEach(year => {
                    const option = document.createElement('option');
                    option.value = year;
                    option.textContent = year;
                    yearSelect.appendChild(option);
                });
                
                yearSelect.disabled = false;
            } catch (error) {
                console.error('Error loading years:', error);
            }
        });
    }
    
    // Handle search button click
    if (searchBtn) {
        searchBtn.addEventListener('click', function() {
            const brandId = brandSelect.value;
            const modelId = modelSelect.value;
            const year = yearSelect.value;
            
            // Build query string
            const params = new URLSearchParams();
            if (brandId) params.append('brand_id', brandId);
            if (modelId) params.append('model_id', modelId);
            if (year) params.append('year', year);
            
            // Redirect to products page with filters
            window.location.href = `/shop/products?${params.toString()}`;
        });
    }
}

/**
 * Initialize quantity controls
 */
function initQuantityControls() {
    document.querySelectorAll('.quantity-control').forEach(control => {
        const minusBtn = control.querySelector('.quantity-minus');
        const plusBtn = control.querySelector('.quantity-plus');
        const input = control.querySelector('.quantity-input');
        
        if (minusBtn) {
            minusBtn.addEventListener('click', function() {
                let value = parseInt(input.value);
                if (value > 1) {
                    input.value = value - 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
        }
        
        if (plusBtn) {
            plusBtn.addEventListener('click', function() {
                let value = parseInt(input.value);
                const max = parseInt(input.max) || 999;
                
                if (value < max) {
                    input.value = value + 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
        }
        
        if (input) {
            input.addEventListener('change', function() {
                let value = parseInt(this.value);
                const min = parseInt(this.min) || 1;
                const max = parseInt(this.max) || 999;
                
                if (isNaN(value) || value < min) {
                    this.value = min;
                } else if (value > max) {
                    this.value = max;
                }
            });
        }
    });
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    // Bootstrap forms validation
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
    
    // Password strength indicator
    const passwordInput = document.getElementById('password');
    if (passwordInput) {
        const strengthIndicator = document.getElementById('password-strength');
        
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            let strength = 0;
            let feedback = '';
            
            // Length check
            if (password.length >= 8) strength++;
            if (password.length >= 12) strength++;
            
            // Complexity checks
            if (/[A-Z]/.test(password)) strength++;
            if (/[0-9]/.test(password)) strength++;
            if (/[^A-Za-z0-9]/.test(password)) strength++;
            
            // Update indicator
            if (strengthIndicator) {
                const strengthText = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong', 'Very Strong'];
                const strengthClass = ['danger', 'danger', 'warning', 'info', 'success', 'success'];
                
                strengthIndicator.textContent = strengthText[strength];
                strengthIndicator.className = `badge bg-${strengthClass[strength]}`;
            }
        });
    }
}

/**
 * Initialize mobile menu
 */
function initMobileMenu() {
    // Close mobile menu when clicking outside
    document.addEventListener('click', function(event) {
        const navbar = document.querySelector('.navbar-collapse');
        const toggle = document.querySelector('.navbar-toggler');
        
        if (navbar && navbar.classList.contains('show') && 
            !navbar.contains(event.target) && 
            (!toggle || !toggle.contains(event.target))) {
            const bsCollapse = new bootstrap.Collapse(navbar);
            bsCollapse.hide();
        }
    });
    
    // Add smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            if (href !== '#') {
                e.preventDefault();
                
                const target = document.querySelector(href);
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            }
        });
    });
}

/**
 * Initialize scroll to top button
 */
function initScrollToTop() {
    const scrollBtn = document.createElement('button');
    scrollBtn.innerHTML = '<i class="fas fa-chevron-up"></i>';
    scrollBtn.className = 'btn btn-primary btn-lg shadow scroll-to-top';
    scrollBtn.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        display: none;
    `;
    
    document.body.appendChild(scrollBtn);
    
    // Show/hide button based on scroll position
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollBtn.style.display = 'flex';
            scrollBtn.style.alignItems = 'center';
            scrollBtn.style.justifyContent = 'center';
        } else {
            scrollBtn.style.display = 'none';
        }
    });
    
    // Scroll to top on click
    scrollBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/**
 * Initialize lazy loading for images
 */
function initLazyLoading() {
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img[data-src]');
        
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    
                    if (img.dataset.srcset) {
                        img.srcset = img.dataset.srcset;
                    }
                    
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    } else {
        // Fallback for browsers without IntersectionObserver
        document.querySelectorAll('img[data-src]').forEach(img => {
            img.src = img.dataset.src;
            if (img.dataset.srcset) {
                img.srcset = img.dataset.srcset;
            }
        });
    }
}

/**
 * Initialize notifications system
 */
function initNotifications() {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
        const askPermission = document.getElementById('ask-notification-permission');
        if (askPermission) {
            askPermission.style.display = 'block';
            
            askPermission.addEventListener('click', async function() {
                const permission = await Notification.requestPermission();
                
                if (permission === 'granted') {
                    showNotification('Notifications enabled!', 'success');
                    this.style.display = 'none';
                    
                    // Subscribe to push notifications
                    subscribeToPushNotifications();
                } else if (permission === 'denied') {
                    showNotification('Notifications blocked. You can enable them in browser settings.', 'warning');
                    this.style.display = 'none';
                }
            });
        }
    }
    
    // Subscribe to push notifications
    async function subscribeToPushNotifications() {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            try {
                const registration = await navigator.serviceWorker.ready;
                const subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: urlBase64ToUint8Array('{{ VAPID_PUBLIC_KEY }}')
                });
                
                // Send subscription to server
                await fetch('/notifications/subscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(subscription)
                });
                
                console.log('Subscribed to push notifications');
            } catch (error) {
                console.error('Failed to subscribe to push notifications:', error);
            }
        }
    }
    
    // Helper function for VAPID key conversion
    function urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');
        
        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);
        
        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
}

/**
 * Show notification toast
 */
function showNotification(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 350px;
        `;
        document.body.appendChild(toastContainer);
    }
    
    // Create toast
    const toastId = 'toast-' + Date.now();
    const toast = document.createElement('div');
    toast.id = toastId;
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.style.cssText = `
        animation: notificationSlideIn 0.3s ease-out;
    `;
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getNotificationIcon(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast, {
        autohide: true,
        delay: 5000
    });
    
    bsToast.show();
    
    // Remove toast from DOM after hiding
    toast.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
    
    // Auto-hide after 5 seconds
    setTimeout(() => {
        bsToast.hide();
    }, 5000);
}

/**
 * Get appropriate icon for notification type
 */
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    
    return icons[type] || 'info-circle';
}

/**
 * Format price with currency symbol
 */
function formatPrice(amount) {
    return `₹${parseFloat(amount).toFixed(2)}`;
}

/**
 * Debounce function for performance
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function for performance
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for use in other modules
window.AutoSpareHub = {
    showNotification,
    formatPrice,
    updateCartCount,
    updateCartTotals
};
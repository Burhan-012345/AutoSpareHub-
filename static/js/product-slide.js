/**
 * Product Detail Slide Animation
 */

document.addEventListener('DOMContentLoaded', function() {
    initProductSlideAnimation();
    initImageGallery();
    initProductTabs();
});

/**
 * Initialize product slide animation
 */
function initProductSlideAnimation() {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Don't trigger if clicking on buttons inside the card
            if (e.target.closest('.btn') || e.target.closest('.wishlist-btn')) {
                return;
            }
            
            const productLink = this.querySelector('a[href*="/product/"]');
            if (productLink) {
                e.preventDefault();
                
                // Get product URL
                const productUrl = productLink.href;
                
                // Show loading overlay
                showLoadingOverlay();
                
                // Fetch product data
                fetch(productUrl)
                    .then(response => response.text())
                    .then(html => {
                        // Create temporary container
                        const tempDiv = document.createElement('div');
                        tempDiv.innerHTML = html;
                        
                        // Extract product detail content
                        const productDetail = tempDiv.querySelector('.product-detail-container');
                        
                        if (productDetail) {
                            // Create modal for product detail
                            createProductModal(productDetail);
                            
                            // Add slide animation
                            setTimeout(() => {
                                const modalContent = document.querySelector('.product-detail-modal .modal-content');
                                if (modalContent) {
                                    modalContent.classList.add('product-detail-slide');
                                }
                            }, 50);
                        }
                    })
                    .catch(error => {
                        console.error('Error loading product:', error);
                        // Fallback to normal navigation
                        window.location.href = productLink.href;
                    })
                    .finally(() => {
                        hideLoadingOverlay();
                    });
            }
        });
    });
}

/**
 * Show loading overlay
 */
function showLoadingOverlay() {
    let overlay = document.getElementById('loading-overlay');
    
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.9);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
        `;
        
        const spinner = document.createElement('div');
        spinner.className = 'spinner';
        spinner.style.cssText = `
            width: 50px;
            height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #0A1F44;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        `;
        
        overlay.appendChild(spinner);
        document.body.appendChild(overlay);
    }
    
    overlay.style.display = 'flex';
}

/**
 * Hide loading overlay
 */
function hideLoadingOverlay() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
    }
}

/**
 * Create product modal
 */
function createProductModal(content) {
    // Remove existing modal
    const existingModal = document.querySelector('.product-detail-modal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'modal fade product-detail-modal';
    modal.tabIndex = -1;
    modal.style.cssText = `
        z-index: 99999;
    `;
    
    modal.innerHTML = `
        <div class="modal-dialog modal-lg modal-dialog-centered">
            <div class="modal-content border-0">
                <div class="modal-header border-0">
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body p-0">
                    ${content.innerHTML}
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Initialize modal
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
    
    // Initialize product features inside modal
    initProductFeatures();
    
    // Handle modal close
    modal.addEventListener('hidden.bs.modal', function() {
        setTimeout(() => {
            modal.remove();
        }, 300);
    });
}

/**
 * Initialize image gallery
 */
function initImageGallery() {
    const mainImage = document.getElementById('main-product-image');
    const thumbnails = document.querySelectorAll('.product-thumbnail');
    
    if (!mainImage || !thumbnails.length) return;
    
    thumbnails.forEach(thumbnail => {
        thumbnail.addEventListener('click', function() {
            // Update main image
            const newSrc = this.dataset.image || this.src;
            mainImage.src = newSrc;
            
            // Update active thumbnail
            thumbnails.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            
            // Add fade animation
            mainImage.style.opacity = '0';
            setTimeout(() => {
                mainImage.style.opacity = '1';
            }, 150);
        });
    });
    
    // Zoom functionality
    if (mainImage) {
        mainImage.addEventListener('mouseenter', function() {
            this.style.cursor = 'zoom-in';
        });
        
        mainImage.addEventListener('click', function() {
            if (this.style.transform === 'scale(2)') {
                this.style.transform = 'scale(1)';
                this.style.cursor = 'zoom-in';
            } else {
                this.style.transform = 'scale(2)';
                this.style.cursor = 'zoom-out';
            }
        });
    }
}

/**
 * Initialize product tabs
 */
function initProductTabs() {
    const tabButtons = document.querySelectorAll('.product-tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const tabId = this.dataset.tab;
            
            // Update active button
            tabButtons.forEach(btn => {
                btn.classList.remove('active');
                btn.setAttribute('aria-selected', 'false');
            });
            this.classList.add('active');
            this.setAttribute('aria-selected', 'true');
            
            // Show active tab content
            const tabContents = document.querySelectorAll('.product-tab-content');
            tabContents.forEach(content => {
                content.classList.remove('active', 'show');
                if (content.id === tabId) {
                    content.classList.add('active', 'show');
                }
            });
        });
    });
}

/**
 * Initialize product features
 */
function initProductFeatures() {
    // Quantity controls
    const quantityInput = document.getElementById('quantity');
    const minusBtn = document.querySelector('.quantity-minus');
    const plusBtn = document.querySelector('.quantity-plus');
    
    if (quantityInput && minusBtn && plusBtn) {
        minusBtn.addEventListener('click', function() {
            let value = parseInt(quantityInput.value);
            if (value > 1) {
                quantityInput.value = value - 1;
            }
        });
        
        plusBtn.addEventListener('click', function() {
            let value = parseInt(quantityInput.value);
            const max = parseInt(quantityInput.max) || 999;
            
            if (value < max) {
                quantityInput.value = value + 1;
            }
        });
    }
    
    // Add to cart button in modal
    const addToCartBtn = document.querySelector('.add-to-cart');
    if (addToCartBtn) {
        addToCartBtn.addEventListener('click', async function() {
            const productId = this.dataset.productId;
            const quantity = document.getElementById('quantity')?.value || 1;
            
            // Show loading
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
                    if (window.AutoSpareHub?.updateCartCount) {
                        window.AutoSpareHub.updateCartCount(data.cart_count);
                    }
                    
                    // Show success animation
                    this.classList.add('cart-add-animation');
                    
                    // Show success message
                    showNotification('Product added to cart!', 'success');
                    
                    // Reset button
                    setTimeout(() => {
                        this.innerHTML = originalText;
                        this.disabled = false;
                        this.classList.remove('cart-add-animation');
                        
                        // Close modal after successful add
                        const modal = document.querySelector('.product-detail-modal');
                        if (modal) {
                            const modalInstance = bootstrap.Modal.getInstance(modal);
                            modalInstance.hide();
                        }
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
    }
    
    // Wishlist button
    const wishlistBtn = document.querySelector('.wishlist-btn');
    if (wishlistBtn) {
        wishlistBtn.addEventListener('click', async function() {
            const productId = this.dataset.productId;
            const isInWishlist = this.classList.contains('active');
            
            try {
                const url = isInWishlist ? 
                    `/wishlist/remove/${productId}` : 
                    `/wishlist/add/${productId}`;
                
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Update button state
                    if (isInWishlist) {
                        this.classList.remove('active');
                        this.innerHTML = '<i class="far fa-heart"></i> Add to Wishlist';
                        showNotification('Removed from wishlist', 'info');
                    } else {
                        this.classList.add('active');
                        this.innerHTML = '<i class="fas fa-heart"></i> In Wishlist';
                        showNotification('Added to wishlist', 'success');
                    }
                } else {
                    showNotification(data.message, 'error');
                }
            } catch (error) {
                console.error('Wishlist error:', error);
                showNotification('Failed to update wishlist', 'error');
            }
        });
    }
    
    // Share button
    const shareBtn = document.querySelector('.share-btn');
    if (shareBtn && navigator.share) {
        shareBtn.style.display = 'block';
        
        shareBtn.addEventListener('click', async function() {
            const productName = document.querySelector('.product-title')?.textContent || '';
            const productUrl = window.location.href;
            
            try {
                await navigator.share({
                    title: productName,
                    text: `Check out this product on AutoSpareHub: ${productName}`,
                    url: productUrl
                });
            } catch (error) {
                console.error('Error sharing:', error);
            }
        });
    }
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification-slide`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 99999;
        max-width: 300px;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

/**
 * Initialize product specifications
 */
function initProductSpecifications() {
    const specs = document.querySelectorAll('.spec-item');
    
    specs.forEach(spec => {
        spec.addEventListener('click', function() {
            this.classList.toggle('expanded');
        });
    });
}

// Initialize when modal content is loaded
document.addEventListener('modalContentLoaded', function() {
    initProductFeatures();
    initProductSpecifications();
});

// Handle browser back button
window.addEventListener('popstate', function() {
    const modal = document.querySelector('.product-detail-modal');
    if (modal) {
        const modalInstance = bootstrap.Modal.getInstance(modal);
        modalInstance.hide();
    }
});
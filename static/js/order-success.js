/**
 * Order Success Animation and Receipt Handling
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations
    initOrderSuccessAnimation();
    initReceiptHandlers();
    
    // Trigger success animation
    triggerSuccessAnimation();
});

/**
 * Initialize order success animation
 */
function initOrderSuccessAnimation() {
    const orderContainer = document.querySelector('.order-success-container');
    if (!orderContainer) return;
    
    // Add confetti effect
    if (document.querySelector('.confetti-container')) {
        createConfetti();
    }
    
    // Start delivery animation
    startDeliveryAnimation();
}

/**
 * Create confetti animation
 */
function createConfetti() {
    const confettiContainer = document.querySelector('.confetti-container');
    if (!confettiContainer) return;
    
    // Create confetti pieces
    for (let i = 0; i < 20; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        
        // Random properties
        const colors = ['#FF8C00', '#0A1F44', '#28A745', '#DC3545', '#FFC107'];
        const color = colors[Math.floor(Math.random() * colors.length)];
        const width = Math.random() * 10 + 5;
        const height = Math.random() * 15 + 5;
        const left = Math.random() * 100;
        const delay = Math.random() * 1000;
        const duration = Math.random() * 1000 + 500;
        
        confetti.style.width = `${width}px`;
        confetti.style.height = `${height}px`;
        confetti.style.left = `${left}%`;
        confetti.style.backgroundColor = color;
        confetti.style.animationDelay = `${delay}ms`;
        confetti.style.animationDuration = `${duration}ms`;
        
        confettiContainer.appendChild(confetti);
    }
}

/**
 * Start delivery animation
 */
function startDeliveryAnimation() {
    const deliveryContainer = document.querySelector('.delivery-animation');
    if (!deliveryContainer) return;
    
    // Reset animation
    const truck = deliveryContainer.querySelector('.delivery-truck');
    const package = deliveryContainer.querySelector('.package');
    
    if (truck && package) {
        // Reset positions
        truck.style.left = '-60px';
        package.style.opacity = '1';
        
        // Start animations
        setTimeout(() => {
            truck.style.animation = 'truckDrive 3s ease-in-out forwards';
            
            // Package pickup animation
            setTimeout(() => {
                package.style.animation = 'packageFloat 2s ease-in-out';
                package.style.opacity = '0';
            }, 1500);
        }, 500);
    }
}

/**
 * Trigger success animation sequence
 */
function triggerSuccessAnimation() {
    const successCheckmark = document.querySelector('.success-checkmark');
    const orderDetails = document.querySelector('.order-details');
    
    if (successCheckmark) {
        successCheckmark.classList.add('animate');
    }
    
    if (orderDetails) {
        setTimeout(() => {
            orderDetails.classList.add('fade-in');
        }, 800);
    }
}

/**
 * Initialize receipt handlers
 */
function initReceiptHandlers() {
    // Print receipt button
    const printBtn = document.getElementById('print-receipt');
    if (printBtn) {
        printBtn.addEventListener('click', printReceipt);
    }
    
    // Download PDF button
    const downloadBtn = document.getElementById('download-invoice');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadInvoice);
    }
    
    // Share order button
    const shareBtn = document.getElementById('share-order');
    if (shareBtn) {
        shareBtn.addEventListener('click', shareOrder);
    }
}

/**
 * Print order receipt
 */
function printReceipt() {
    const receipt = document.getElementById('order-receipt');
    if (!receipt) return;
    
    // Store original styles
    const originalStyles = document.head.innerHTML;
    
    // Create print styles
    const printStyles = `
        <style>
            @media print {
                body * {
                    visibility: hidden;
                }
                #order-receipt, #order-receipt * {
                    visibility: visible;
                }
                #order-receipt {
                    position: absolute;
                    left: 0;
                    top: 0;
                    width: 100%;
                    background: white;
                    box-shadow: none;
                    border: none;
                }
                .no-print {
                    display: none !important;
                }
                .print-only {
                    display: block !important;
                }
            }
        </style>
    `;
    
    // Add print styles
    document.head.innerHTML += printStyles;
    
    // Trigger print
    window.print();
    
    // Restore original styles
    setTimeout(() => {
        document.head.innerHTML = originalStyles;
    }, 100);
}

/**
 * Download invoice as PDF (using html2pdf library)
 */
async function downloadInvoice() {
    const receipt = document.getElementById('order-receipt');
    if (!receipt) return;
    
    // Check if html2pdf is loaded
    if (typeof html2pdf === 'undefined') {
        // Load html2pdf library
        await loadScript('https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js');
    }
    
    // Configure PDF options
    const opt = {
        margin: [10, 10, 10, 10],
        filename: `AutoSpareHub_Invoice_${Date.now()}.pdf`,
        image: { type: 'jpeg', quality: 0.98 },
        html2canvas: { 
            scale: 2,
            useCORS: true,
            logging: true
        },
        jsPDF: { 
            unit: 'mm', 
            format: 'a4', 
            orientation: 'portrait' 
        }
    };
    
    // Generate PDF
    html2pdf().set(opt).from(receipt).save();
    
    // Show download confirmation
    showNotification('Invoice download started!', 'success');
}

/**
 * Share order details
 */
function shareOrder() {
    if (navigator.share) {
        // Use Web Share API
        const orderId = document.getElementById('order-id')?.textContent || 'Order';
        const total = document.getElementById('order-total')?.textContent || '';
        
        navigator.share({
            title: `AutoSpareHub Order: ${orderId}`,
            text: `I just placed an order on AutoSpareHub! Order ID: ${orderId}, Total: ${total}`,
            url: window.location.href
        })
        .then(() => console.log('Order shared successfully'))
        .catch(error => console.log('Error sharing:', error));
    } else {
        // Fallback: Copy to clipboard
        copyOrderToClipboard();
    }
}

/**
 * Copy order details to clipboard
 */
function copyOrderToClipboard() {
    const orderId = document.getElementById('order-id')?.textContent || '';
    const orderDate = document.getElementById('order-date')?.textContent || '';
    const orderTotal = document.getElementById('order-total')?.textContent || '';
    
    const text = `Order ID: ${orderId}\nDate: ${orderDate}\nTotal: ${orderTotal}\n\nThank you for shopping with AutoSpareHub!`;
    
    navigator.clipboard.writeText(text)
        .then(() => {
            showNotification('Order details copied to clipboard!', 'success');
        })
        .catch(err => {
            console.error('Failed to copy: ', err);
            showNotification('Failed to copy order details', 'error');
        });
}

/**
 * Load external script
 */
function loadScript(src) {
    return new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

/**
 * Show notification
 */
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification-slide`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 300px;
    `;
    
    // Add to DOM
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

/**
 * Track order status
 */
function trackOrder() {
    const orderId = document.getElementById('order-id')?.textContent;
    if (!orderId) return;
    
    // Show tracking modal
    const trackingModal = new bootstrap.Modal(document.getElementById('trackingModal'));
    trackingModal.show();
    
    // Simulate tracking updates
    simulateTrackingUpdates(orderId);
}

/**
 * Simulate tracking updates
 */
function simulateTrackingUpdates(orderId) {
    const trackingSteps = document.querySelectorAll('.tracking-step');
    let currentStep = 0;
    
    const interval = setInterval(() => {
        if (currentStep < trackingSteps.length) {
            trackingSteps[currentStep].classList.add('completed');
            currentStep++;
        } else {
            clearInterval(interval);
        }
    }, 1000);
}

/**
 * Continue shopping button handler
 */
document.getElementById('continue-shopping')?.addEventListener('click', function() {
    // Add animation to button
    this.classList.add('pulse');
    
    // Redirect after animation
    setTimeout(() => {
        window.location.href = '/shop';
    }, 500);
});

/**
 * View order details button handler
 */
document.getElementById('view-order-details')?.addEventListener('click', function() {
    const orderId = document.getElementById('order-id')?.textContent;
    if (orderId) {
        window.location.href = `/user/orders/${orderId}`;
    }
});

/**
 * Initialize PWA install prompt
 */
if ('serviceWorker' in navigator && 'BeforeInstallPromptEvent' in window) {
    let deferredPrompt;
    
    window.addEventListener('beforeinstallprompt', (e) => {
        // Prevent Chrome 67 and earlier from automatically showing the prompt
        e.preventDefault();
        // Stash the event so it can be triggered later
        deferredPrompt = e;
        
        // Show install button
        const installBtn = document.getElementById('install-app');
        if (installBtn) {
            installBtn.style.display = 'block';
            installBtn.addEventListener('click', installApp);
        }
    });
    
    function installApp() {
        if (!deferredPrompt) return;
        
        // Show the install prompt
        deferredPrompt.prompt();
        
        // Wait for the user to respond to the prompt
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === 'accepted') {
                console.log('User accepted the install prompt');
            } else {
                console.log('User dismissed the install prompt');
            }
            deferredPrompt = null;
            
            // Hide install button
            const installBtn = document.getElementById('install-app');
            if (installBtn) {
                installBtn.style.display = 'none';
            }
        });
    }
}

// Add event listener for offline/online status
window.addEventListener('online', () => {
    showNotification('You are back online!', 'success');
});

window.addEventListener('offline', () => {
    showNotification('You are offline. Some features may not work.', 'warning');
});

/**
 * Initialize lazy loading for images
 */
if ('IntersectionObserver' in window) {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
}
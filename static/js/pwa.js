/**
 * PWA (Progressive Web App) functionality for AutoSpareHub
 */

class PWAHandler {
    constructor() {
        this.deferredPrompt = null;
        this.isStandalone = window.matchMedia('(display-mode: standalone)').matches;
        this.init();
    }
    
    init() {
        // Register service worker
        this.registerServiceWorker();
        
        // Handle install prompt
        this.handleInstallPrompt();
        
        // Handle offline/online status
        this.handleNetworkStatus();
        
        // Handle app launch
        this.handleAppLaunch();
    }
    
    /**
     * Register service worker
     */
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/service-worker.js');
                console.log('Service Worker registered:', registration);
                
                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    console.log('New service worker found:', newWorker);
                    
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();
                        }
                    });
                });
                
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    }
    
    /**
     * Handle install prompt
     */
    handleInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            // Prevent Chrome 67 and earlier from automatically showing the prompt
            e.preventDefault();
            
            // Stash the event so it can be triggered later
            this.deferredPrompt = e;
            
            // Show install button
            this.showInstallButton();
            
            // Log install prompt event
            console.log('Install prompt available');
        });
        
        // Listen for app installation
        window.addEventListener('appinstalled', () => {
            console.log('App installed successfully');
            this.deferredPrompt = null;
            this.hideInstallButton();
            
            // Track installation in analytics
            this.trackInstallation();
        });
    }
    
    /**
     * Show install button
     */
    showInstallButton() {
        // Check if we should show the install button
        if (this.shouldShowInstallPrompt()) {
            const installBtn = document.getElementById('install-app-btn');
            if (installBtn) {
                installBtn.style.display = 'block';
                installBtn.addEventListener('click', () => this.installApp());
            }
            
            // Also create a floating install button if not exists
            this.createFloatingInstallButton();
        }
    }
    
    /**
     * Hide install button
     */
    hideInstallButton() {
        const installBtn = document.getElementById('install-app-btn');
        if (installBtn) {
            installBtn.style.display = 'none';
        }
        
        const floatingBtn = document.getElementById('floating-install-btn');
        if (floatingBtn) {
            floatingBtn.remove();
        }
    }
    
    /**
     * Create floating install button
     */
    createFloatingInstallButton() {
        if (document.getElementById('floating-install-btn')) return;
        
        const floatingBtn = document.createElement('button');
        floatingBtn.id = 'floating-install-btn';
        floatingBtn.innerHTML = `
            <i class="fas fa-download me-2"></i>
            Install App
        `;
        floatingBtn.className = 'btn btn-primary shadow-lg';
        floatingBtn.style.cssText = `
            position: fixed;
            bottom: 80px;
            right: 20px;
            z-index: 9999;
            border-radius: 25px;
            padding: 10px 20px;
            animation: pulse 2s infinite;
        `;
        
        floatingBtn.addEventListener('click', () => this.installApp());
        document.body.appendChild(floatingBtn);
        
        // Auto-hide after 30 seconds
        setTimeout(() => {
            if (floatingBtn.parentNode) {
                floatingBtn.remove();
            }
        }, 30000);
    }
    
    /**
     * Check if we should show install prompt
     */
    shouldShowInstallPrompt() {
        // Don't show if already installed
        if (this.isStandalone) return false;
        
        // Don't show on iOS (handled differently)
        if (this.isIOS()) return false;
        
        // Check if user has dismissed before
        const dismissed = localStorage.getItem('install_prompt_dismissed');
        if (dismissed) {
            const dismissedTime = parseInt(dismissed);
            const oneWeekAgo = Date.now() - (7 * 24 * 60 * 60 * 1000);
            return dismissedTime < oneWeekAgo;
        }
        
        return true;
    }
    
    /**
     * Install the app
     */
    async installApp() {
        if (!this.deferredPrompt) {
            console.log('No install prompt available');
            return;
        }
        
        // Show the install prompt
        this.deferredPrompt.prompt();
        
        // Wait for the user to respond to the prompt
        const { outcome } = await this.deferredPrompt.userChoice;
        
        console.log(`User response to install prompt: ${outcome}`);
        
        // Clear the saved prompt
        this.deferredPrompt = null;
        
        // Hide install button
        this.hideInstallButton();
        
        // Track the outcome
        if (outcome === 'accepted') {
            console.log('User accepted the install prompt');
            this.trackEvent('app_install', 'accepted');
        } else {
            console.log('User dismissed the install prompt');
            this.trackEvent('app_install', 'dismissed');
            
            // Store dismissal time
            localStorage.setItem('install_prompt_dismissed', Date.now().toString());
        }
    }
    
    /**
     * Handle network status
     */
    handleNetworkStatus() {
        // Update UI based on network status
        const updateOnlineStatus = () => {
            const isOnline = navigator.onLine;
            
            if (isOnline) {
                this.hideOfflineIndicator();
                this.syncOfflineData();
            } else {
                this.showOfflineIndicator();
            }
            
            // Dispatch custom event
            document.dispatchEvent(new CustomEvent('networkStatusChange', {
                detail: { isOnline }
            }));
        };
        
        // Listen for network status changes
        window.addEventListener('online', updateOnlineStatus);
        window.addEventListener('offline', updateOnlineStatus);
        
        // Initial check
        updateOnlineStatus();
    }
    
    /**
     * Show offline indicator
     */
    showOfflineIndicator() {
        let indicator = document.getElementById('offline-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'offline-indicator';
            indicator.innerHTML = `
                <div class="alert alert-warning alert-dismissible fade show mb-0" role="alert">
                    <i class="fas fa-wifi-slash me-2"></i>
                    You are currently offline. Some features may not work.
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `;
            indicator.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                z-index: 9999;
            `;
            document.body.prepend(indicator);
        }
    }
    
    /**
     * Hide offline indicator
     */
    hideOfflineIndicator() {
        const indicator = document.getElementById('offline-indicator');
        if (indicator) {
            indicator.remove();
        }
    }
    
    /**
     * Sync offline data
     */
    async syncOfflineData() {
        if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
            try {
                // Request sync for offline data
                const registration = await navigator.serviceWorker.ready;
                
                if ('sync' in registration) {
                    await registration.sync.register('sync-cart');
                    console.log('Background sync registered');
                }
                
                // Check for pending requests
                await this.processPendingRequests();
                
            } catch (error) {
                console.error('Sync error:', error);
            }
        }
    }
    
    /**
     * Process pending requests
     */
    async processPendingRequests() {
        // In a real implementation, this would process requests
        // that were queued while offline
        console.log('Processing pending requests...');
    }
    
    /**
     * Handle app launch
     */
    handleAppLaunch() {
        // Check if app was launched from home screen
        if (window.navigator.standalone || this.isStandalone) {
            console.log('App launched from home screen');
            this.trackEvent('app_launch', 'home_screen');
            
            // Add standalone class for CSS adjustments
            document.documentElement.classList.add('standalone');
        } else {
            console.log('App launched in browser');
            this.trackEvent('app_launch', 'browser');
        }
        
        // Handle launch parameters
        this.handleLaunchParameters();
    }
    
    /**
     * Handle launch parameters
     */
    handleLaunchParameters() {
        // Check URL parameters for deep links
        const urlParams = new URLSearchParams(window.location.search);
        
        // Handle product deep links
        const productId = urlParams.get('product');
        if (productId) {
            // Navigate to product page
            window.location.href = `/shop/product/${productId}`;
        }
        
        // Handle order deep links
        const orderId = urlParams.get('order');
        if (orderId) {
            // Navigate to order page
            window.location.href = `/user/orders/${orderId}`;
        }
    }
    
    /**
     * Show update notification
     */
    showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show';
        notification.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <i class="fas fa-sync-alt me-2"></i>
                    A new version is available. Refresh to update.
                </div>
                <button type="button" class="btn btn-sm btn-outline-info" id="refresh-app">
                    Refresh Now
                </button>
            </div>
        `;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        document.body.appendChild(notification);
        
        // Handle refresh button
        document.getElementById('refresh-app').addEventListener('click', () => {
            window.location.reload();
        });
        
        // Auto-dismiss after 30 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 30000);
    }
    
    /**
     * Add to home screen for iOS
     */
    showiOSInstallInstructions() {
        if (!this.isIOS()) return;
        
        const isSafari = /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
        const isStandalone = window.navigator.standalone;
        
        if (isSafari && !isStandalone) {
            const instructions = document.createElement('div');
            instructions.className = 'alert alert-info';
            instructions.innerHTML = `
                <div class="d-flex align-items-center">
                    <i class="fas fa-mobile-alt fa-2x me-3"></i>
                    <div>
                        <h6 class="mb-1">Install AutoSpareHub</h6>
                        <p class="mb-0 small">
                            Tap <i class="fas fa-share"></i> then "Add to Home Screen"
                        </p>
                    </div>
                    <button type="button" class="btn-close ms-auto" data-bs-dismiss="alert"></button>
                </div>
            `;
            
            const container = document.querySelector('.container') || document.body;
            container.prepend(instructions);
        }
    }
    
    /**
     * Check if device is iOS
     */
    isIOS() {
        return [
            'iPad Simulator',
            'iPhone Simulator',
            'iPod Simulator',
            'iPad',
            'iPhone',
            'iPod'
        ].includes(navigator.platform) ||
        (navigator.userAgent.includes("Mac") && "ontouchend" in document);
    }
    
    /**
     * Track events
     */
    trackEvent(category, action, label = null) {
        // Implement analytics tracking
        console.log(`Tracking: ${category} - ${action}${label ? ` - ${label}` : ''}`);
        
        // Example: Send to Google Analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', action, {
                'event_category': category,
                'event_label': label
            });
        }
    }
    
    /**
     * Track installation
     */
    trackInstallation() {
        this.trackEvent('app', 'installed');
        
        // Store installation timestamp
        localStorage.setItem('app_installed', Date.now().toString());
    }
    
    /**
     * Check if app is installed
     */
    isAppInstalled() {
        return localStorage.getItem('app_installed') !== null || this.isStandalone;
    }
    
    /**
     * Get app version
     */
    getAppVersion() {
        return '1.0.0'; // This should come from manifest or package.json
    }
    
    /**
     * Clear app cache
     */
    async clearCache() {
        if ('caches' in window) {
            const cacheNames = await caches.keys();
            await Promise.all(
                cacheNames.map(cacheName => caches.delete(cacheName))
            );
            console.log('Cache cleared');
        }
    }
    
    /**
     * Check for updates
     */
    async checkForUpdates() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.ready;
                await registration.update();
                console.log('Update check completed');
            } catch (error) {
                console.error('Update check failed:', error);
            }
        }
    }
    
    /**
     * Request notification permission
     */
    async requestNotificationPermission() {
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                console.log('Notification permission granted');
                this.trackEvent('notifications', 'permission_granted');
                return true;
            } else {
                console.log('Notification permission denied');
                this.trackEvent('notifications', 'permission_denied');
                return false;
            }
        }
        return false;
    }
    
    /**
     * Subscribe to push notifications
     */
    async subscribeToPushNotifications() {
        if ('serviceWorker' in navigator && 'PushManager' in window) {
            try {
                const registration = await navigator.serviceWorker.ready;
                
                // Subscribe to push notifications
                const subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.urlBase64ToUint8Array('{{ VAPID_PUBLIC_KEY }}')
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
                return true;
                
            } catch (error) {
                console.error('Failed to subscribe to push notifications:', error);
                return false;
            }
        }
        return false;
    }
    
    /**
     * Convert VAPID key
     */
    urlBase64ToUint8Array(base64String) {
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

// Initialize PWA when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.pwa = new PWAHandler();
    
    // Add PWA-specific CSS
    const style = document.createElement('style');
    style.textContent = `
        @media (display-mode: standalone) {
            /* Adjustments for standalone mode */
            header {
                padding-top: env(safe-area-inset-top);
            }
            
            .standalone-padding {
                padding-bottom: env(safe-area-inset-bottom);
            }
            
            /* Hide browser UI elements */
            .browser-only {
                display: none !important;
            }
        }
        
        /* Install button styles */
        #install-app-btn {
            transition: all 0.3s ease;
        }
        
        #install-app-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Offline indicator animation */
        @keyframes pulse {
            0% {
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(10, 31, 68, 0.7);
            }
            70% {
                transform: scale(1.05);
                box-shadow: 0 0 0 10px rgba(10, 31, 68, 0);
            }
            100% {
                transform: scale(1);
                box-shadow: 0 0 0 0 rgba(10, 31, 68, 0);
            }
        }
    `;
    document.head.appendChild(style);
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWAHandler;
}
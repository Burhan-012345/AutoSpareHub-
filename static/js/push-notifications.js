/**
 * Push Notifications Handler for AutoSpareHub
 */

class PushNotificationHandler {
    constructor() {
        this.publicVapidKey = document.querySelector('meta[name="vapid-public-key"]')?.content;
        this.isSubscribed = false;
        this.registration = null;
        this.init();
    }
    
    async init() {
        // Check browser support
        if (!this.isSupported()) {
            console.log('Push notifications not supported');
            return;
        }
        
        // Get service worker registration
        this.registration = await navigator.serviceWorker.ready;
        
        // Check current subscription
        await this.checkSubscription();
        
        // Request permission if not already done
        await this.requestPermission();
        
        // Listen for push events
        this.listenForPushEvents();
    }
    
    /**
     * Check if push notifications are supported
     */
    isSupported() {
        return 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
    }
    
    /**
     * Check current subscription status
     */
    async checkSubscription() {
        if (!this.registration) return;
        
        const subscription = await this.registration.pushManager.getSubscription();
        this.isSubscribed = !(subscription === null);
        
        // Update UI based on subscription status
        this.updateSubscriptionUI();
        
        return subscription;
    }
    
    /**
     * Request notification permission
     */
    async requestPermission() {
        if (Notification.permission === 'default') {
            // Don't request automatically - let user click a button
            return;
        }
        
        if (Notification.permission === 'denied') {
            console.log('Notification permission denied');
            this.showPermissionBlockedMessage();
            return;
        }
        
        if (Notification.permission === 'granted') {
            console.log('Notification permission already granted');
            await this.subscribe();
        }
    }
    
    /**
     * Subscribe to push notifications
     */
    async subscribe() {
        if (!this.publicVapidKey) {
            console.error('VAPID public key not found');
            this.showError('Push notifications not configured');
            return;
        }
        
        if (!this.registration) {
            console.error('Service worker not registered');
            this.showError('Service worker not available');
            return;
        }
        
        try {
            // Subscribe to push notifications
            const subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlBase64ToUint8Array(this.publicVapidKey)
            });
            
            // Send subscription to server
            const response = await fetch('/notifications/subscribe', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(subscription)
            });
            
            if (!response.ok) {
                throw new Error('Failed to save subscription');
            }
            
            this.isSubscribed = true;
            this.updateSubscriptionUI();
            
            console.log('Subscribed to push notifications');
            this.showSuccess('Notifications enabled successfully!');
            
            // Track subscription
            this.trackEvent('push_notifications', 'subscribed');
            
        } catch (error) {
            console.error('Failed to subscribe:', error);
            
            if (error.name === 'NotAllowedError') {
                this.showError('Notification permission denied');
            } else {
                this.showError('Failed to enable notifications');
            }
            
            this.trackEvent('push_notifications', 'subscribe_failed', error.message);
        }
    }
    
    /**
     * Unsubscribe from push notifications
     */
    async unsubscribe() {
        if (!this.registration) return;
        
        try {
            const subscription = await this.registration.pushManager.getSubscription();
            
            if (subscription) {
                // Unsubscribe locally
                await subscription.unsubscribe();
                
                // Notify server
                await fetch('/notifications/unsubscribe', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ endpoint: subscription.endpoint })
                });
                
                this.isSubscribed = false;
                this.updateSubscriptionUI();
                
                console.log('Unsubscribed from push notifications');
                this.showSuccess('Notifications disabled');
                
                this.trackEvent('push_notifications', 'unsubscribed');
            }
            
        } catch (error) {
            console.error('Failed to unsubscribe:', error);
            this.showError('Failed to disable notifications');
        }
    }
    
    /**
     * Toggle subscription
     */
    async toggleSubscription() {
        if (this.isSubscribed) {
            await this.unsubscribe();
        } else {
            await this.subscribe();
        }
    }
    
    /**
     * Update UI based on subscription status
     */
    updateSubscriptionUI() {
        const enableBtn = document.getElementById('enable-notifications');
        const disableBtn = document.getElementById('disable-notifications');
        const statusEl = document.getElementById('notification-status');
        
        if (enableBtn) {
            enableBtn.style.display = this.isSubscribed ? 'none' : 'block';
        }
        
        if (disableBtn) {
            disableBtn.style.display = this.isSubscribed ? 'block' : 'none';
        }
        
        if (statusEl) {
            if (Notification.permission === 'denied') {
                statusEl.innerHTML = `
                    <span class="badge bg-danger">
                        <i class="fas fa-ban me-1"></i>Blocked
                    </span>
                    <small class="text-muted ms-2">Enable in browser settings</small>
                `;
            } else if (this.isSubscribed) {
                statusEl.innerHTML = `
                    <span class="badge bg-success">
                        <i class="fas fa-bell me-1"></i>Enabled
                    </span>
                `;
            } else {
                statusEl.innerHTML = `
                    <span class="badge bg-secondary">
                        <i class="fas fa-bell-slash me-1"></i>Disabled
                    </span>
                `;
            }
        }
    }
    
    /**
     * Listen for push events
     */
    listenForPushEvents() {
        // Listen for incoming push notifications
        navigator.serviceWorker.addEventListener('message', (event) => {
            const data = event.data;
            
            if (data.type === 'PUSH_RECEIVED') {
                console.log('Push notification received:', data);
                this.handlePushNotification(data.payload);
            }
        });
        
        // Listen for notification clicks
        navigator.serviceWorker.addEventListener('notificationclick', (event) => {
            this.handleNotificationClick(event);
        });
        
        // Listen for notification close
        navigator.serviceWorker.addEventListener('notificationclose', (event) => {
            console.log('Notification closed:', event.notification.tag);
        });
    }
    
    /**
     * Handle push notification
     */
    handlePushNotification(payload) {
        // Show notification using the Notification API
        if (Notification.permission === 'granted') {
            const options = {
                body: payload.body,
                icon: payload.icon || '/static/images/icons/icon-192x192.png',
                badge: payload.badge || '/static/images/icons/icon-192x192.png',
                tag: payload.tag,
                data: payload.data,
                requireInteraction: payload.requireInteraction || false,
                actions: payload.actions || [
                    {
                        action: 'view',
                        title: 'View'
                    },
                    {
                        action: 'close',
                        title: 'Close'
                    }
                ]
            };
            
            // Show notification
            const notification = new Notification(payload.title, options);
            
            // Handle notification click
            notification.onclick = (event) => {
                event.preventDefault();
                this.handleNotificationAction('view', payload.data);
                notification.close();
            };
            
            // Handle action buttons
            if ('actions' in Notification.prototype) {
                notification.onaction = (event) => {
                    this.handleNotificationAction(event.action, payload.data);
                };
            }
        }
    }
    
    /**
     * Handle notification click from service worker
     */
    handleNotificationClick(event) {
        event.notification.close();
        
        const action = event.action;
        const data = event.notification.data;
        
        this.handleNotificationAction(action, data);
    }
    
    /**
     * Handle notification action
     */
    handleNotificationAction(action, data) {
        switch (action) {
            case 'view':
            case '':
                // Handle based on notification type
                this.handleNotificationData(data);
                break;
                
            case 'order':
                if (data.order_id) {
                    window.location.href = `/user/orders/${data.order_id}`;
                }
                break;
                
            case 'product':
                if (data.product_id) {
                    window.location.href = `/shop/product/${data.product_id}`;
                }
                break;
                
            case 'close':
                // Do nothing
                break;
        }
        
        // Track notification interaction
        this.trackEvent('push_notifications', 'clicked', action);
    }
    
    /**
     * Handle notification data
     */
    handleNotificationData(data) {
        if (!data) return;
        
        // Handle different notification types
        switch (data.type) {
            case 'order_placed':
                if (data.order_id) {
                    window.location.href = `/user/orders/${data.order_id}`;
                }
                break;
                
            case 'order_status':
                if (data.order_id) {
                    window.location.href = `/user/orders/${data.order_id}`;
                }
                break;
                
            case 'new_product':
                if (data.product_id) {
                    window.location.href = `/shop/product/${data.product_id}`;
                }
                break;
                
            case 'cart_reminder':
                window.location.href = '/cart';
                break;
                
            case 'promotion':
                window.location.href = '/shop?promo=true';
                break;
                
            default:
                // Default to homepage
                window.location.href = '/';
        }
    }
    
    /**
     * Show permission blocked message
     */
    showPermissionBlockedMessage() {
        const message = `
            <div class="alert alert-warning">
                <h6><i class="fas fa-ban me-2"></i>Notifications Blocked</h6>
                <p class="mb-2">To enable notifications:</p>
                <ol class="mb-0">
                    <li>Click the lock icon in your browser's address bar</li>
                    <li>Change "Notifications" to "Allow"</li>
                    <li>Refresh this page</li>
                </ol>
            </div>
        `;
        
        this.showMessage(message, 'permission-blocked');
    }
    
    /**
     * Show message
     */
    showMessage(content, id = null) {
        let container = document.getElementById('notification-messages');
        
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-messages';
            container.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 9999;
                max-width: 400px;
            `;
            document.body.appendChild(container);
        }
        
        const messageDiv = document.createElement('div');
        if (id) messageDiv.id = id;
        messageDiv.innerHTML = content;
        messageDiv.className = 'mb-2';
        
        container.appendChild(messageDiv);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.remove();
            }
        }, 10000);
    }
    
    /**
     * Show success message
     */
    showSuccess(message) {
        this.showMessage(`
            <div class="alert alert-success alert-dismissible fade show">
                <i class="fas fa-check-circle me-2"></i>${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
    }
    
    /**
     * Show error message
     */
    showError(message) {
        this.showMessage(`
            <div class="alert alert-danger alert-dismissible fade show">
                <i class="fas fa-exclamation-circle me-2"></i>${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `);
    }
    
    /**
     * Send test notification
     */
    async sendTestNotification() {
        try {
            const response = await fetch('/notifications/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    title: 'Test Notification',
                    body: 'This is a test notification from AutoSpareHub',
                    icon: '/static/images/icons/icon-192x192.png'
                })
            });
            
            if (response.ok) {
                this.showSuccess('Test notification sent!');
            } else {
                throw new Error('Failed to send test');
            }
            
        } catch (error) {
            console.error('Failed to send test:', error);
            this.showError('Failed to send test notification');
        }
    }
    
    /**
     * Track event
     */
    trackEvent(category, action, label = null) {
        // Implement analytics tracking
        console.log(`Tracking: ${category} - ${action}${label ? ` - ${label}` : ''}`);
        
        if (typeof gtag !== 'undefined') {
            gtag('event', action, {
                'event_category': category,
                'event_label': label
            });
        }
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
    
    /**
     * Get subscription info
     */
    async getSubscriptionInfo() {
        if (!this.registration) return null;
        
        const subscription = await this.registration.pushManager.getSubscription();
        
        if (!subscription) return null;
        
        return {
            endpoint: subscription.endpoint,
            expirationTime: subscription.expirationTime,
            keys: subscription.toJSON().keys
        };
    }
    
    /**
     * Check if notifications are enabled
     */
    isEnabled() {
        return this.isSubscribed && Notification.permission === 'granted';
    }
}

// Initialize push notifications when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if push notifications should be initialized
    const shouldInitialize = document.querySelector('meta[name="enable-push"]')?.content === 'true';
    
    if (shouldInitialize && 'serviceWorker' in navigator) {
        window.pushHandler = new PushNotificationHandler();
        
        // Add VAPID public key to meta tag if not present
        if (!document.querySelector('meta[name="vapid-public-key"]')) {
            const meta = document.createElement('meta');
            meta.name = 'vapid-public-key';
            meta.content = '{{ VAPID_PUBLIC_KEY }}'; // This should be replaced by the server
            document.head.appendChild(meta);
        }
    }
    
    // Add notification settings UI if not present
    addNotificationSettingsUI();
});

/**
 * Add notification settings UI
 */
function addNotificationSettingsUI() {
    // Check if settings container exists
    if (document.getElementById('notification-settings')) return;
    
    // Create settings container
    const container = document.createElement('div');
    container.id = 'notification-settings';
    container.className = 'd-none';
    container.innerHTML = `
        <div class="card">
            <div class="card-header">
                <h5 class="mb-0">
                    <i class="fas fa-bell me-2"></i>Notification Settings
                </h5>
            </div>
            <div class="card-body">
                <div class="mb-3">
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="notify-orders">
                        <label class="form-check-label" for="notify-orders">
                            Order updates
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="notify-promotions">
                        <label class="form-check-label" for="notify-promotions">
                            Promotions & offers
                        </label>
                    </div>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="notify-products">
                        <label class="form-check-label" for="notify-products">
                            New products
                        </label>
                    </div>
                </div>
                <div class="d-grid gap-2">
                    <button type="button" class="btn btn-primary" id="save-notification-settings">
                        Save Settings
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(container);
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PushNotificationHandler;
}
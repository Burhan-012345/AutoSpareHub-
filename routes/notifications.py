"""
Push notification routes for AutoSpareHub
"""

import json
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from pywebpush import webpush, WebPushException
from app import db
from models import PushSubscription, User
import os

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/subscribe', methods=['POST'])
@login_required
def subscribe():
    """Subscribe user to push notifications"""
    try:
        subscription_data = request.get_json()
        
        if not subscription_data:
            return jsonify({'success': False, 'message': 'No subscription data provided'})
        
        # Check if subscription already exists
        existing = PushSubscription.query.filter_by(
            user_id=current_user.id,
            endpoint=subscription_data.get('endpoint')
        ).first()
        
        if existing:
            return jsonify({'success': True, 'message': 'Already subscribed'})
        
        # Save subscription
        subscription = PushSubscription(
            user_id=current_user.id,
            endpoint=subscription_data.get('endpoint'),
            p256dh=subscription_data['keys']['p256dh'],
            auth=subscription_data['keys']['auth']
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Subscribed to notifications'})
    
    except Exception as e:
        current_app.logger.error(f'Subscription error: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500

@notifications_bp.route('/unsubscribe', methods=['POST'])
@login_required
def unsubscribe():
    """Unsubscribe user from push notifications"""
    try:
        subscription_data = request.get_json()
        
        if not subscription_data:
            return jsonify({'success': False, 'message': 'No subscription data provided'})
        
        # Remove subscription
        subscription = PushSubscription.query.filter_by(
            user_id=current_user.id,
            endpoint=subscription_data.get('endpoint')
        ).first()
        
        if subscription:
            db.session.delete(subscription)
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Unsubscribed from notifications'})
    
    except Exception as e:
        current_app.logger.error(f'Unsubscription error: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500

@notifications_bp.route('/send', methods=['POST'])
@login_required
def send_notification():
    """Send push notification to user"""
    try:
        if not current_user.is_admin():
            return jsonify({'success': False, 'message': 'Unauthorized'}), 403
        
        data = request.get_json()
        user_id = data.get('user_id')
        title = data.get('title')
        body = data.get('body')
        url = data.get('url')
        
        if not all([user_id, title, body]):
            return jsonify({'success': False, 'message': 'Missing required fields'})
        
        # Send to specific user
        success = send_push_notification(user_id, title, body, {'url': url})
        
        if success:
            return jsonify({'success': True, 'message': 'Notification sent'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send notification'})
    
    except Exception as e:
        current_app.logger.error(f'Notification send error: {e}')
        return jsonify({'success': False, 'message': str(e)}), 500

def send_push_notification(user_id, title, body, data=None):
    """Send push notification to user"""
    try:
        # Get user's subscriptions
        subscriptions = PushSubscription.query.filter_by(user_id=user_id).all()
        
        if not subscriptions:
            return False
        
        vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY')
        vapid_claim_email = current_app.config.get('VAPID_CLAIM_EMAIL')
        
        if not vapid_private_key or not vapid_claim_email:
            current_app.logger.error('VAPID keys not configured')
            return False
        
        vapid_claims = {
            "sub": vapid_claim_email
        }
        
        success_count = 0
        
        for subscription in subscriptions:
            try:
                # Prepare notification payload
                payload = {
                    'title': title,
                    'body': body,
                    'icon': '/static/images/icon-192x192.png',
                    'badge': '/static/images/icon-192x192.png',
                    'data': data or {}
                }
                
                # Send push notification
                webpush(
                    subscription_info={
                        'endpoint': subscription.endpoint,
                        'keys': {
                            'p256dh': subscription.p256dh,
                            'auth': subscription.auth
                        }
                    },
                    data=json.dumps(payload),
                    vapid_private_key=vapid_private_key,
                    vapid_claims=vapid_claims
                )
                
                success_count += 1
                
            except WebPushException as e:
                if e.response and e.response.status_code == 410:
                    # Subscription expired, remove it
                    db.session.delete(subscription)
                else:
                    current_app.logger.error(f'Push notification error: {e}')
        
        if success_count > 0:
            db.session.commit()
            return True
        
        return False
    
    except Exception as e:
        current_app.logger.error(f'Push notification send error: {e}')
        return False

def send_order_notifications(order, notification_type):
    """Send notifications for order events"""
    user_id = order.user_id
    order_number = order.order_number
    
    notifications = {
        'placed': {
            'title': 'Order Placed Successfully!',
            'body': f'Your order {order_number} has been placed successfully.',
            'data': {'order_id': order.id, 'type': 'order_placed'}
        },
        'confirmed': {
            'title': 'Order Confirmed',
            'body': f'Your order {order_number} has been confirmed.',
            'data': {'order_id': order.id, 'type': 'order_confirmed'}
        },
        'packed': {
            'title': 'Order Packed',
            'body': f'Your order {order_number} has been packed and is ready for shipping.',
            'data': {'order_id': order.id, 'type': 'order_packed'}
        },
        'shipped': {
            'title': 'Order Shipped',
            'body': f'Your order {order_number} has been shipped.',
            'data': {'order_id': order.id, 'type': 'order_shipped'}
        },
        'delivered': {
            'title': 'Order Delivered',
            'body': f'Your order {order_number} has been delivered.',
            'data': {'order_id': order.id, 'type': 'order_delivered'}
        },
        'cancelled': {
            'title': 'Order Cancelled',
            'body': f'Your order {order_number} has been cancelled.',
            'data': {'order_id': order.id, 'type': 'order_cancelled'}
        }
    }
    
    if notification_type in notifications:
        notification = notifications[notification_type]
        send_push_notification(user_id, notification['title'], notification['body'], notification['data'])
        
        # Also send admin notification for new orders
        if notification_type == 'placed':
            admin_users = User.query.filter_by(role='admin').all()
            for admin in admin_users:
                send_push_notification(
                    admin.id,
                    'New Order Received',
                    f'New order {order_number} has been placed.',
                    {'order_id': order.id, 'type': 'new_order'}
                )
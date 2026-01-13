"""
Cart and checkout routes for AutoSpareHub
"""

from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from decimal import Decimal
from app import db, mail
from models import Cart, Product, Order, OrderItem, Address, OrderStatusHistory
from forms import AddressForm, CheckoutForm
from flask_mail import Message

cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/')
@login_required
def view_cart():
    """View shopping cart"""
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    
    # Calculate totals
    subtotal = Decimal('0')
    for item in cart_items:
        subtotal += item.product.discounted_price * item.quantity
    
    # Get tax and shipping from config
    from config import Config
    tax_rate = Config.TAX_RATE
    shipping_rate = Config.SHIPPING_RATE
    
    tax_amount = subtotal * Decimal(str(tax_rate))
    shipping_amount = Decimal(str(shipping_rate))
    total = subtotal + tax_amount + shipping_amount
    
    return render_template('cart/cart.html',
                         cart_items=cart_items,
                         subtotal=subtotal,
                         tax_amount=tax_amount,
                         shipping_amount=shipping_amount,
                         total=total)

@cart_bp.route('/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    """Add product to cart"""
    product = Product.query.get_or_404(product_id)
    
    # Check stock
    quantity = request.form.get('quantity', 1, type=int)
    
    if quantity < 1:
        return jsonify({'success': False, 'message': 'Invalid quantity'})
    
    if product.stock_quantity < quantity:
        return jsonify({'success': False, 'message': 'Insufficient stock'})
    
    # Check if product already in cart
    cart_item = Cart.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if cart_item:
        # Update quantity
        new_quantity = cart_item.quantity + quantity
        if product.stock_quantity < new_quantity:
            return jsonify({'success': False, 'message': 'Insufficient stock'})
        cart_item.quantity = new_quantity
    else:
        # Add new item to cart
        cart_item = Cart(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    
    # Get updated cart count
    cart_count = Cart.query.filter_by(user_id=current_user.id).count()
    
    return jsonify({
        'success': True,
        'message': 'Product added to cart',
        'cart_count': cart_count
    })

@cart_bp.route('/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    """Update cart item quantity"""
    cart_item = Cart.query.get_or_404(item_id)
    
    # Verify ownership
    if cart_item.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    quantity = request.form.get('quantity', type=int)
    
    if not quantity or quantity < 1:
        return jsonify({'success': False, 'message': 'Invalid quantity'})
    
    # Check stock
    if cart_item.product.stock_quantity < quantity:
        return jsonify({'success': False, 'message': 'Insufficient stock'})
    
    cart_item.quantity = quantity
    db.session.commit()
    
    # Calculate new totals
    subtotal = cart_item.product.discounted_price * quantity
    
    return jsonify({
        'success': True,
        'subtotal': float(subtotal),
        'item_total': float(subtotal)
    })

@cart_bp.route('/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_cart(item_id):
    """Remove item from cart"""
    cart_item = Cart.query.get_or_404(item_id)
    
    # Verify ownership
    if cart_item.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db.session.delete(cart_item)
    db.session.commit()
    
    # Get updated cart count
    cart_count = Cart.query.filter_by(user_id=current_user.id).count()
    
    return jsonify({
        'success': True,
        'message': 'Item removed from cart',
        'cart_count': cart_count
    })

@cart_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Checkout process"""
    # Check if cart is empty
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart.view_cart'))
    
    # Check stock availability
    for item in cart_items:
        if item.product.stock_quantity < item.quantity:
            flash(f'Insufficient stock for {item.product.name}. Only {item.product.stock_quantity} available.', 'danger')
            return redirect(url_for('cart.view_cart'))
    
    # Get user addresses
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    form = CheckoutForm()
    
    # Populate address choices
    form.address_id.choices = [(addr.id, addr.full_name) for addr in addresses]
    
    if form.validate_on_submit():
        # Get selected address
        address = Address.query.get(form.address_id.data)
        if not address or address.user_id != current_user.id:
            flash('Invalid address selected.', 'danger')
            return redirect(url_for('cart.checkout'))
        
        # Calculate totals
        from config import Config
        
        subtotal = Decimal('0')
        for item in cart_items:
            subtotal += item.product.discounted_price * item.quantity
        
        tax_amount = subtotal * Decimal(str(Config.TAX_RATE))
        shipping_amount = Decimal(str(Config.SHIPPING_RATE))
        total_amount = subtotal + tax_amount + shipping_amount
        
        # Create order
        order = Order(
            order_number=Order.generate_order_number(),
            user_id=current_user.id,
            address_id=address.id,
            subtotal=subtotal,
            tax_amount=tax_amount,
            shipping_amount=shipping_amount,
            total_amount=total_amount,
            payment_method=form.payment_method.data,
            notes=form.notes.data
        )
        
        db.session.add(order)
        db.session.flush()  # Get order ID without committing
        
        # Create order items and update stock
        for cart_item in cart_items:
            # Create order item
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product.id,
                product_name=cart_item.product.name,
                part_number=cart_item.product.part_number,
                quantity=cart_item.quantity,
                unit_price=cart_item.product.discounted_price,
                total_price=cart_item.product.discounted_price * cart_item.quantity
            )
            db.session.add(order_item)
            
            # Update product stock
            cart_item.product.decrease_stock(cart_item.quantity)
            
            # Remove from cart
            db.session.delete(cart_item)
        
        # Create initial status history
        status_history = OrderStatusHistory(
            order_id=order.id,
            status='pending',
            notes='Order placed successfully'
        )
        db.session.add(status_history)
        
        # Commit transaction
        db.session.commit()
        
        # Send order confirmation email
        send_order_confirmation_email(order)
        
        # Send admin notification
        send_admin_order_notification(order)
        
        # Clear cart from session
        session.pop('cart', None)
        
        # Redirect to order confirmation page
        return redirect(url_for('cart.order_confirmation', order_id=order.id))
    
    # Calculate totals for display
    subtotal = Decimal('0')
    for item in cart_items:
        subtotal += item.product.discounted_price * item.quantity
    
    from config import Config
    tax_amount = subtotal * Decimal(str(Config.TAX_RATE))
    shipping_amount = Decimal(str(Config.SHIPPING_RATE))
    total = subtotal + tax_amount + shipping_amount
    
    return render_template('cart/checkout.html',
                         form=form,
                         cart_items=cart_items,
                         addresses=addresses,
                         subtotal=subtotal,
                         tax_amount=tax_amount,
                         shipping_amount=shipping_amount,
                         total=total)

@cart_bp.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    """Order confirmation page with animation"""
    order = Order.query.get_or_404(order_id)
    
    # Verify ownership
    if order.user_id != current_user.id and not current_user.is_admin():
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('index'))
    
    return render_template('cart/order_confirmation.html',
                         order=order,
                         timedelta=timedelta)

@cart_bp.route('/address/add', methods=['GET', 'POST'])
@login_required
def add_address():
    """Add new shipping address"""
    form = AddressForm()
    
    if form.validate_on_submit():
        # Check if this should be default address
        if form.is_default.data:
            # Remove default from other addresses
            Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
        
        address = Address(
            user_id=current_user.id,
            full_name=form.full_name.data,
            phone=form.phone.data,
            address_line1=form.address_line1.data,
            address_line2=form.address_line2.data,
            city=form.city.data,
            state=form.state.data,
            postal_code=form.postal_code.data,
            country=form.country.data,
            is_default=form.is_default.data
        )
        
        db.session.add(address)
        db.session.commit()
        
        flash('Address added successfully.', 'success')
        
        # Redirect back to checkout if coming from there
        if request.args.get('from_checkout'):
            return redirect(url_for('cart.checkout'))
        return redirect(url_for('user.profile'))
    
    return render_template('cart/add_address.html', form=form)

@cart_bp.route('/api/cart/count')
@login_required
def get_cart_count():
    """Get cart item count (API)"""
    count = Cart.query.filter_by(user_id=current_user.id).count()
    return jsonify({'count': count})

@cart_bp.route('/api/cart/total')
@login_required
def get_cart_total():
    """Get cart total amount (API)"""
    cart_items = Cart.query.filter_by(user_id=current_user.id).all()
    
    subtotal = Decimal('0')
    for item in cart_items:
        subtotal += item.product.discounted_price * item.quantity
    
    from config import Config
    tax_amount = subtotal * Decimal(str(Config.TAX_RATE))
    shipping_amount = Decimal(str(Config.SHIPPING_RATE))
    total = subtotal + tax_amount + shipping_amount
    
    return jsonify({
        'subtotal': float(subtotal),
        'tax': float(tax_amount),
        'shipping': float(shipping_amount),
        'total': float(total)
    })

# Email Functions
def send_order_confirmation_email(order):
    """Send order confirmation email to customer"""
    try:
        from flask import current_app
        from app import mail
        
        msg = Message(
            subject=f'Order Confirmation - {order.order_number}',
            recipients=[order.user.email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.html = render_template(
            'email/order_confirmation.html',
            order=order,
            user=order.user,
            app_name=current_app.config['APP_NAME']
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send order confirmation email: {e}')
        return False

def send_admin_order_notification(order):
    """Send notification email to admin about new order"""
    try:
        from flask import current_app
        from app import mail
        
        msg = Message(
            subject=f'New Order Received - {order.order_number}',
            recipients=[current_app.config['ADMIN_EMAIL']],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.html = render_template(
            'email/admin_order_notification.html',
            order=order,
            user=order.user,
            app_name=current_app.config['APP_NAME']
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send admin notification email: {e}')
        return False
"""
User profile and account management routes
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from models import User, Order, Address, Wishlist, Review
from forms import AddressForm

user_bp = Blueprint('user', __name__)

@user_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = User.query.get(current_user.id)
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    # Get recent orders
    recent_orders = Order.query.filter_by(user_id=current_user.id)\
        .order_by(Order.created_at.desc()).limit(5).all()
    
    # Get wishlist count
    wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()
    
    # Get cart count
    cart_count = sum(item.quantity for item in current_user.cart_items)
    
    return render_template('user/profile.html',
                         user=user,
                         addresses=addresses,
                         recent_orders=recent_orders,
                         wishlist_count=wishlist_count,
                         cart_count=cart_count)

@user_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if name and phone:
            current_user.name = name
            current_user.phone = phone
            
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('user.profile'))
        else:
            flash('Please fill in all required fields.', 'danger')
    
    return render_template('user/edit_profile.html')

@user_bp.route('/orders')
@login_required
def orders():
    """User order history"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    orders = Order.query.filter_by(user_id=current_user.id)\
        .order_by(Order.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('user/orders.html', orders=orders)

@user_bp.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail view"""
    order = Order.query.get_or_404(order_id)
    
    # Verify ownership
    if order.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('user.orders'))
    
    return render_template('user/order_detail.html', order=order)

@user_bp.route('/addresses')
@login_required
def addresses():
    """User addresses management"""
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template('user/addresses.html', addresses=addresses)

@user_bp.route('/address/add', methods=['GET', 'POST'])
@login_required
def add_address():
    """Add new address"""
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
        return redirect(url_for('user.addresses'))
    
    return render_template('user/add_address.html', form=form)

@user_bp.route('/address/edit/<int:address_id>', methods=['GET', 'POST'])
@login_required
def edit_address(address_id):
    """Edit existing address"""
    address = Address.query.get_or_404(address_id)
    
    # Verify ownership
    if address.user_id != current_user.id:
        flash('Unauthorized access.', 'danger')
        return redirect(url_for('user.addresses'))
    
    form = AddressForm(obj=address)
    
    if form.validate_on_submit():
        # Check if this should be default address
        if form.is_default.data:
            # Remove default from other addresses
            Address.query.filter_by(user_id=current_user.id, is_default=True)\
                .filter(Address.id != address_id).update({'is_default': False})
        
        address.full_name = form.full_name.data
        address.phone = form.phone.data
        address.address_line1 = form.address_line1.data
        address.address_line2 = form.address_line2.data
        address.city = form.city.data
        address.state = form.state.data
        address.postal_code = form.postal_code.data
        address.country = form.country.data
        address.is_default = form.is_default.data
        
        db.session.commit()
        
        flash('Address updated successfully.', 'success')
        return redirect(url_for('user.addresses'))
    
    return render_template('user/edit_address.html', form=form, address=address)

@user_bp.route('/address/delete/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    """Delete address"""
    address = Address.query.get_or_404(address_id)
    
    # Verify ownership
    if address.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    db.session.delete(address)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Address deleted'})

@user_bp.route('/address/set-default/<int:address_id>', methods=['POST'])
@login_required
def set_default_address(address_id):
    """Set address as default"""
    address = Address.query.get_or_404(address_id)
    
    # Verify ownership
    if address.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'})
    
    # Remove default from other addresses
    Address.query.filter_by(user_id=current_user.id, is_default=True)\
        .filter(Address.id != address_id).update({'is_default': False})
    
    # Set this address as default
    address.is_default = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Default address updated'})

@user_bp.route('/wishlist')
@login_required
def wishlist():
    """User wishlist"""
    wishlist_items = Wishlist.query.filter_by(user_id=current_user.id).all()
    products = [item.product for item in wishlist_items]
    
    return render_template('user/wishlist.html', products=products)

@user_bp.route('/reviews')
@login_required
def reviews():
    """User reviews"""
    reviews = Review.query.filter_by(user_id=current_user.id)\
        .order_by(Review.created_at.desc()).all()
    
    return render_template('user/reviews.html', reviews=reviews)

@user_bp.route('/notifications')
@login_required
def notifications():
    """User notifications"""
    return render_template('user/notifications.html')

@user_bp.route('/settings')
@login_required
def settings():
    """User settings"""
    return render_template('user/settings.html')

@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    # Validate inputs
    if not all([current_password, new_password, confirm_password]):
        return jsonify({'success': False, 'message': 'All fields are required'})
    
    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match'})
    
    if len(new_password) < 8:
        return jsonify({'success': False, 'message': 'Password must be at least 8 characters'})
    
    # Verify current password
    if not current_user.verify_password(current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect'})
    
    # Update password
    current_user.password = new_password
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Password changed successfully'})

@user_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account"""
    password = request.form.get('password')
    
    if not password:
        return jsonify({'success': False, 'message': 'Password is required'})
    
    # Verify password
    if not current_user.verify_password(password):
        return jsonify({'success': False, 'message': 'Incorrect password'})
    
    # Soft delete user (set inactive)
    current_user.is_active = False
    db.session.commit()
    
    # Logout user
    from flask_login import logout_user
    logout_user()
    
    return jsonify({'success': True, 'message': 'Account deleted successfully'})

@user_bp.route('/api/profile-stats')
@login_required
def profile_stats():
    """Get user profile statistics (API)"""
    # Order stats
    total_orders = Order.query.filter_by(user_id=current_user.id).count()
    delivered_orders = Order.query.filter_by(
        user_id=current_user.id,
        order_status='delivered'
    ).count()
    
    # Wishlist count
    wishlist_count = Wishlist.query.filter_by(user_id=current_user.id).count()
    
    # Reviews count
    reviews_count = Review.query.filter_by(user_id=current_user.id).count()
    
    # Total spent
    total_spent = db.session.query(db.func.sum(Order.total_amount))\
        .filter_by(user_id=current_user.id, order_status='delivered')\
        .scalar() or 0
    
    return jsonify({
        'total_orders': total_orders,
        'delivered_orders': delivered_orders,
        'wishlist_count': wishlist_count,
        'reviews_count': reviews_count,
        'total_spent': float(total_spent)
    })
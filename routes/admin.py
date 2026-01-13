"""
Admin routes for AutoSpareHub
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app import db
from models import User, Product, Category, Order, OrderItem, OrderStatusHistory, VehicleBrand, VehicleModel
from forms import ProductForm, CategoryForm, VehicleBrandForm, VehicleModelForm

admin_bp = Blueprint('admin', __name__)

def admin_required(func):
    """Decorator to require admin role"""
    from functools import wraps
    
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin():
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('index'))
        return func(*args, **kwargs)
    
    return decorated_view

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    
    # Calculate total sales
    total_sales = db.session.query(func.sum(Order.total_amount)).scalar() or 0
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    # Get low stock products
    low_stock_products = Product.query.filter(
        Product.stock_quantity > 0,
        Product.stock_quantity <= 10
    ).order_by(Product.stock_quantity.asc()).limit(10).all()
    
    # Get sales data for chart (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    daily_sales = db.session.query(
        func.date(Order.created_at).label('date'),
        func.sum(Order.total_amount).label('total')
    ).filter(
        Order.created_at >= thirty_days_ago
    ).group_by(
        func.date(Order.created_at)
    ).order_by(
        func.date(Order.created_at)
    ).all()
    
    # Prepare chart data
    sales_dates = [sale.date.strftime('%Y-%m-%d') for sale in daily_sales]
    sales_totals = [float(sale.total) for sale in daily_sales]
    
    # Get order status distribution
    status_counts = db.session.query(
        Order.order_status,
        func.count(Order.id).label('count')
    ).group_by(Order.order_status).all()
    
    status_labels = [status[0] for status in status_counts]
    status_data = [status[1] for status in status_counts]
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         total_sales=total_sales,
                         recent_orders=recent_orders,
                         low_stock_products=low_stock_products,
                         sales_dates=sales_dates,
                         sales_totals=sales_totals,
                         status_labels=status_labels,
                         status_data=status_data)

@admin_bp.route('/products')
@login_required
@admin_required
def products():
    """Product management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    products = Product.query.order_by(Product.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    categories = Category.query.all()
    brands = VehicleBrand.query.all()
    models = VehicleModel.query.all()
    
    return render_template('admin/products.html',
                         products=products,
                         categories=categories,
                         brands=brands,
                         models=models)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    """Add new product"""
    form = ProductForm()
    
    # Populate category choices
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.brand_id.choices = [('', 'Select Brand')] + [(b.id, b.name) for b in VehicleBrand.query.all()]
    form.model_id.choices = [('', 'Select Model')] + [(m.id, m.name) for m in VehicleModel.query.all()]
    
    if form.validate_on_submit():
        # Check if part number already exists
        existing = Product.query.filter_by(part_number=form.part_number.data).first()
        if existing:
            flash('Part number already exists.', 'danger')
            return render_template('admin/add_product.html', form=form)
        
        # Create slug from product name
        from slugify import slugify
        slug = slugify(form.name.data)
        
        # Check if slug exists
        counter = 1
        original_slug = slug
        while Product.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        # Create product
        product = Product(
            name=form.name.data,
            part_number=form.part_number.data,
            slug=slug,
            category_id=form.category_id.data,
            brand_id=form.brand_id.data if form.brand_id.data else None,
            model_id=form.model_id.data if form.model_id.data else None,
            manufacturing_year=form.manufacturing_year.data,
            price=form.price.data,
            discount=form.discount.data or 0,
            stock_quantity=form.stock_quantity.data,
            description=form.description.data,
            is_active=form.is_active.data
        )
        
        db.session.add(product)
        db.session.flush()  # Get product ID
        
        # Handle image upload
        if form.images.data:
            for image in form.images.data:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    filepath = os.path.join(
                        current_app.config['UPLOAD_FOLDER'],
                        f"product_{product.id}_{filename}"
                    )
                    image.save(filepath)
                    
                    # Save relative path
                    image_url = f"/static/images/products/product_{product.id}_{filename}"
                    
                    # Create product image record
                    from models import ProductImage
                    product_image = ProductImage(
                        product_id=product.id,
                        image_url=image_url,
                        is_primary=False  # First image is primary
                    )
                    db.session.add(product_image)
        
        # Set first image as primary if no primary set
        if product.images and not any(img.is_primary for img in product.images):
            product.images[0].is_primary = True
        
        db.session.commit()
        
        flash('Product added successfully.', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/add_product.html', form=form)

@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    """Edit product"""
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    
    # Populate category choices
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    form.brand_id.choices = [('', 'Select Brand')] + [(b.id, b.name) for b in VehicleBrand.query.all()]
    form.model_id.choices = [('', 'Select Model')] + [(m.id, m.name) for m in VehicleModel.query.all()]
    
    if form.validate_on_submit():
        # Update product
        product.name = form.name.data
        product.part_number = form.part_number.data
        product.category_id = form.category_id.data
        product.brand_id = form.brand_id.data if form.brand_id.data else None
        product.model_id = form.model_id.data if form.model_id.data else None
        product.manufacturing_year = form.manufacturing_year.data
        product.price = form.price.data
        product.discount = form.discount.data or 0
        product.stock_quantity = form.stock_quantity.data
        product.description = form.description.data
        product.is_active = form.is_active.data
        
        # Handle image upload
        if form.images.data:
            for image in form.images.data:
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    filepath = os.path.join(
                        current_app.config['UPLOAD_FOLDER'],
                        f"product_{product.id}_{filename}"
                    )
                    image.save(filepath)
                    
                    # Save relative path
                    image_url = f"/static/images/products/product_{product.id}_{filename}"
                    
                    # Create product image record
                    from models import ProductImage
                    product_image = ProductImage(
                        product_id=product.id,
                        image_url=image_url,
                        is_primary=False
                    )
                    db.session.add(product_image)
        
        db.session.commit()
        
        flash('Product updated successfully.', 'success')
        return redirect(url_for('admin.products'))
    
    return render_template('admin/edit_product.html', form=form, product=product)

@admin_bp.route('/products/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    """Delete product"""
    product = Product.query.get_or_404(product_id)
    
    # Soft delete by setting inactive
    product.is_active = False
    db.session.commit()
    
    flash('Product deactivated successfully.', 'success')
    return redirect(url_for('admin.products'))

@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    """Order management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    status_filter = request.args.get('status')
    
    query = Order.query
    
    if status_filter:
        query = query.filter_by(order_status=status_filter)
    
    orders = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/orders.html', orders=orders)

@admin_bp.route('/orders/<int:order_id>')
@login_required
@admin_required
def order_detail(order_id):
    """Order detail view"""
    order = Order.query.get_or_404(order_id)
    
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/update-status/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def update_order_status(order_id):
    """Update order status"""
    order = Order.query.get_or_404(order_id)
    
    new_status = request.form.get('status')
    notes = request.form.get('notes', '')
    tracking_number = request.form.get('tracking_number')
    
    if new_status not in ['pending', 'confirmed', 'packed', 'shipped', 'delivered', 'cancelled']:
        return jsonify({'success': False, 'message': 'Invalid status'})
    
    # Update order
    order.order_status = new_status
    
    if tracking_number:
        order.tracking_number = tracking_number
    
    # Add status history
    status_history = OrderStatusHistory(
        order_id=order.id,
        status=new_status,
        notes=notes
    )
    db.session.add(status_history)
    
    db.session.commit()
    
    # Send status update email to customer
    send_order_status_email(order, new_status, notes)
    
    # Send push notification
    from routes.notifications import send_push_notification
    send_push_notification(
        user_id=order.user_id,
        title='Order Status Updated',
        body=f'Your order {order.order_number} is now {new_status}',
        data={'order_id': order.id, 'status': new_status}
    )
    
    return jsonify({'success': True, 'message': 'Order status updated'})

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """User management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    """Category management"""
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_category():
    """Add new category"""
    form = CategoryForm()
    
    # Populate parent category choices
    form.parent_id.choices = [('', 'No Parent')] + [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        # Create slug
        from slugify import slugify
        slug = slugify(form.name.data)
        
        # Check if slug exists
        counter = 1
        original_slug = slug
        while Category.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{counter}"
            counter += 1
        
        category = Category(
            name=form.name.data,
            slug=slug,
            description=form.description.data,
            parent_id=form.parent_id.data if form.parent_id.data else None
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category added successfully.', 'success')
        return redirect(url_for('admin.categories'))
    
    return render_template('admin/add_category.html', form=form)

@admin_bp.route('/reviews')
@login_required
@admin_required
def reviews():
    """Review management"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    reviews = Review.query.order_by(Review.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/reviews.html', reviews=reviews)

@admin_bp.route('/reviews/approve/<int:review_id>', methods=['POST'])
@login_required
@admin_required
def approve_review(review_id):
    """Approve review"""
    review = Review.query.get_or_404(review_id)
    
    review.is_approved = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Review approved'})

@admin_bp.route('/reviews/reject/<int:review_id>', methods=['POST'])
@login_required
@admin_required
def reject_review(review_id):
    """Reject review"""
    review = Review.query.get_or_404(review_id)
    
    db.session.delete(review)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Review rejected'})

@admin_bp.route('/api/stats')
@login_required
@admin_required
def get_stats():
    """Get dashboard statistics (API)"""
    # Today's sales
    today = datetime.utcnow().date()
    today_sales = db.session.query(func.sum(Order.total_amount)).filter(
        func.date(Order.created_at) == today
    ).scalar() or 0
    
    # This month's sales
    month_start = datetime.utcnow().replace(day=1)
    month_sales = db.session.query(func.sum(Order.total_amount)).filter(
        Order.created_at >= month_start
    ).scalar() or 0
    
    # Pending orders
    pending_orders = Order.query.filter_by(order_status='pending').count()
    
    # Low stock products count
    low_stock_count = Product.query.filter(
        Product.stock_quantity > 0,
        Product.stock_quantity <= 5
    ).count()
    
    return jsonify({
        'today_sales': float(today_sales),
        'month_sales': float(month_sales),
        'pending_orders': pending_orders,
        'low_stock_count': low_stock_count
    })

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def send_order_status_email(order, status, notes):
    """Send order status update email"""
    try:
        from flask import render_template
        from app import mail
        
        msg = Message(
            subject=f'Order Status Update - {order.order_number}',
            recipients=[order.user.email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.html = render_template(
            'email/order_status_update.html',
            order=order,
            status=status,
            notes=notes,
            app_name=current_app.config['APP_NAME']
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send status update email: {e}')
        return False
"""
Shop routes for AutoSpareHub
"""

from flask import Blueprint, render_template, request, jsonify, flash, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from app import db
from models import Product, Category, VehicleBrand, VehicleModel, Wishlist, Review
from forms import SearchForm
import math

shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/')
def index():
    """Shop homepage with featured products"""
    # Get featured products (in stock, with discount)
    featured_products = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity > 0,
        Product.discount > 0
    ).order_by(db.func.random()).limit(8).all()
    
    # Get new arrivals
    new_arrivals = Product.query.filter(
        Product.is_active == True,
        Product.stock_quantity > 0
    ).order_by(Product.created_at.desc()).limit(8).all()
    
    # Get categories
    categories = Category.query.filter_by(parent_id=None).all()
    
    # Get vehicle brands
    brands = VehicleBrand.query.all()
    
    return render_template('shop/index.html',
                         featured_products=featured_products,
                         new_arrivals=new_arrivals,
                         categories=categories,
                         brands=brands)

@shop_bp.route('/products')
def products():
    """Product listing with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Base query
    query = Product.query.filter(Product.is_active == True)
    
    # Category filter
    category_id = request.args.get('category_id', type=int)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # Brand filter
    brand_id = request.args.get('brand_id', type=int)
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    
    # Model filter
    model_id = request.args.get('model_id', type=int)
    if model_id:
        query = query.filter(Product.model_id == model_id)
    
    # Year filter
    year = request.args.get('year')
    if year:
        query = query.filter(Product.manufacturing_year == year)
    
    # Price range filter
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Search query
    search_query = request.args.get('q')
    if search_query:
        query = query.filter(or_(
            Product.name.ilike(f'%{search_query}%'),
            Product.part_number.ilike(f'%{search_query}%'),
            Product.description.ilike(f'%{search_query}%')
        ))
    
    # Sort order
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    
    if sort_by == 'price':
        if sort_order == 'asc':
            query = query.order_by(Product.price.asc())
        else:
            query = query.order_by(Product.price.desc())
    elif sort_by == 'name':
        query = query.order_by(Product.name.asc())
    elif sort_by == 'discount':
        query = query.order_by(Product.discount.desc())
    else:  # created_at
        query = query.order_by(Product.created_at.desc())
    
    # Pagination
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items
    
    # Get filter data
    categories = Category.query.all()
    brands = VehicleBrand.query.all()
    
    # Get years from products
    years = db.session.query(Product.manufacturing_year).distinct().all()
    years = [year[0] for year in years if year[0]]
    
    return render_template('shop/products.html',
                         products=products,
                         pagination=pagination,
                         categories=categories,
                         brands=brands,
                         years=years,
                         search_query=search_query)

@shop_bp.route('/product/<slug>')
def product_detail(slug):
    """Product detail page with slide animation"""
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Get related products (same category)
    related_products = Product.query.filter(
        Product.category_id == product.category_id,
        Product.id != product.id,
        Product.is_active == True,
        Product.stock_quantity > 0
    ).order_by(db.func.random()).limit(4).all()
    
    # Get reviews
    reviews = Review.query.filter_by(
        product_id=product.id,
        is_approved=True
    ).order_by(Review.created_at.desc()).limit(5).all()
    
    # Calculate average rating
    avg_rating = 0
    if reviews:
        avg_rating = sum(review.rating for review in reviews) / len(reviews)
    
    # Check if product is in user's wishlist
    in_wishlist = False
    if current_user.is_authenticated:
        wishlist_item = Wishlist.query.filter_by(
            user_id=current_user.id,
            product_id=product.id
        ).first()
        in_wishlist = wishlist_item is not None
    
    return render_template('shop/product_detail.html',
                         product=product,
                         related_products=related_products,
                         reviews=reviews,
                         avg_rating=avg_rating,
                         in_wishlist=in_wishlist)

@shop_bp.route('/category/<slug>')
def category(slug):
    """Products by category"""
    category = Category.query.filter_by(slug=slug).first_or_404()
    
    # Get all products in this category (including subcategories)
    category_ids = [category.id]
    for subcategory in category.children:
        category_ids.append(subcategory.id)
    
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    products = Product.query.filter(
        Product.category_id.in_(category_ids),
        Product.is_active == True
    ).order_by(Product.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('shop/category.html',
                         category=category,
                         products=products)

@shop_bp.route('/search')
def search():
    """Search products"""
    form = SearchForm()
    
    if form.validate():
        query = form.query.data
        
        # Search in name, part number, and description
        products = Product.query.filter(
            or_(
                Product.name.ilike(f'%{query}%'),
                Product.part_number.ilike(f'%{query}%'),
                Product.description.ilike(f'%{query}%')
            ),
            Product.is_active == True
        ).all()
        
        return render_template('shop/search.html',
                             form=form,
                             products=products,
                             query=query)
    
    return render_template('shop/search.html', form=form)

@shop_bp.route('/api/brands')
def get_brands():
    """Get all vehicle brands (API)"""
    brands = VehicleBrand.query.all()
    return jsonify([{
        'id': brand.id,
        'name': brand.name
    } for brand in brands])

@shop_bp.route('/api/models/<int:brand_id>')
def get_models(brand_id):
    """Get models for a brand (API)"""
    models = VehicleModel.query.filter_by(brand_id=brand_id).all()
    return jsonify([{
        'id': model.id,
        'name': model.name
    } for model in models])

@shop_bp.route('/api/products/by-vehicle')
def get_products_by_vehicle():
    """Get products compatible with specific vehicle"""
    brand_id = request.args.get('brand_id', type=int)
    model_id = request.args.get('model_id', type=int)
    year = request.args.get('year')
    
    query = Product.query.filter(Product.is_active == True)
    
    if brand_id:
        query = query.filter(Product.brand_id == brand_id)
    if model_id:
        query = query.filter(Product.model_id == model_id)
    if year:
        query = query.filter(Product.manufacturing_year == year)
    
    products = query.limit(20).all()
    
    return jsonify([{
        'id': product.id,
        'name': product.name,
        'part_number': product.part_number,
        'price': float(product.price),
        'discounted_price': float(product.discounted_price),
        'image': product.primary_image,
        'in_stock': product.is_in_stock,
        'slug': product.slug
    } for product in products])

@shop_bp.route('/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    """Add product to wishlist"""
    product = Product.query.get_or_404(product_id)
    
    # Check if already in wishlist
    existing = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing:
        return jsonify({'success': False, 'message': 'Product already in wishlist'})
    
    # Add to wishlist
    wishlist_item = Wishlist(
        user_id=current_user.id,
        product_id=product_id
    )
    
    db.session.add(wishlist_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Product added to wishlist'})

@shop_bp.route('/wishlist/remove/<int:product_id>', methods=['POST'])
@login_required
def remove_from_wishlist(product_id):
    """Remove product from wishlist"""
    wishlist_item = Wishlist.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first_or_404()
    
    db.session.delete(wishlist_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Product removed from wishlist'})

@shop_bp.route('/review/add/<int:product_id>', methods=['POST'])
@login_required
def add_review(product_id):
    """Add product review"""
    product = Product.query.get_or_404(product_id)
    
    # Check if user has purchased this product
    from models import OrderItem, Order
    has_purchased = db.session.query(OrderItem).join(Order).filter(
        Order.user_id == current_user.id,
        OrderItem.product_id == product_id,
        Order.order_status == 'delivered'
    ).first() is not None
    
    if not has_purchased:
        return jsonify({
            'success': False,
            'message': 'You can only review products you have purchased'
        })
    
    # Check if already reviewed
    existing_review = Review.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()
    
    if existing_review:
        return jsonify({
            'success': False,
            'message': 'You have already reviewed this product'
        })
    
    # Get form data
    rating = request.form.get('rating', type=int)
    comment = request.form.get('comment', '')
    
    if not rating or rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'Invalid rating'})
    
    # Create review
    review = Review(
        user_id=current_user.id,
        product_id=product_id,
        order_id=0,  # Should get from actual order
        rating=rating,
        comment=comment,
        is_approved=False  # Admin must approve reviews
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Review submitted for approval'
    })
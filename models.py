"""
Database models for AutoSpareHub
"""

from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='customer')
    email_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    addresses = db.relationship('Address', backref='user', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('Cart', backref='user', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='user', lazy=True)
    push_subscriptions = db.relationship('PushSubscription', backref='user', lazy=True, cascade='all, delete-orphan')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def get_cart_count(self):
        return sum(item.quantity for item in self.cart_items)
    
    def get_cart_total(self):
        from app import create_app
        app = create_app()
        with app.app_context():
            total = 0
            for item in self.cart_items:
                total += item.product.price * item.quantity
            return total
    
    def __repr__(self):
        return f'<User {self.email}>'

class PasswordResetToken(db.Model):
    """Password reset token model"""
    __tablename__ = 'password_reset_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_valid(self):
        return datetime.utcnow() < self.expires_at and not self.used
    
    @staticmethod
    def create_token(user_id, expiration=3600):
        import secrets
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(seconds=expiration)
        
        # Invalidate old tokens for this user
        PasswordResetToken.query.filter_by(user_id=user_id, used=False).update({'used': True})
        
        new_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.session.add(new_token)
        db.session.commit()
        return token

class Category(db.Model):
    """Product category model"""
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Self-referential relationship
    parent = db.relationship('Category', remote_side=[id], backref='children')
    products = db.relationship('Product', backref='category', lazy=True)
    
    def __repr__(self):
        return f'<Category {self.name}>'

class VehicleBrand(db.Model):
    """Vehicle brand model"""
    __tablename__ = 'vehicle_brands'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    logo = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    models = db.relationship('VehicleModel', backref='brand', lazy=True, cascade='all, delete-orphan')
    products = db.relationship('Product', backref='vehicle_brand', lazy=True)
    
    def __repr__(self):
        return f'<VehicleBrand {self.name}>'

class VehicleModel(db.Model):
    """Vehicle model model"""
    __tablename__ = 'vehicle_models'
    
    id = db.Column(db.Integer, primary_key=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('vehicle_brands.id'), nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    products = db.relationship('Product', backref='vehicle_model', lazy=True)
    
    def __repr__(self):
        return f'<VehicleModel {self.name}>'

class Product(db.Model):
    """Product model"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    part_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    brand_id = db.Column(db.Integer, db.ForeignKey('vehicle_brands.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('vehicle_models.id'))
    manufacturing_year = db.Column(db.String(20))
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(5, 2), default=0)
    stock_quantity = db.Column(db.Integer, default=0)
    description = db.Column(db.Text)
    specifications = db.Column(db.JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    images = db.relationship('ProductImage', backref='product', lazy=True, cascade='all, delete-orphan')
    cart_items = db.relationship('Cart', backref='product', lazy=True)
    order_items = db.relationship('OrderItem', backref='product', lazy=True)
    
    @property
    def discounted_price(self):
        if self.discount:
            return self.price * (1 - self.discount / 100)
        return self.price
    
    @property
    def primary_image(self):
        primary = ProductImage.query.filter_by(product_id=self.id, is_primary=True).first()
        if primary:
            return primary.image_url
        # Return first image or placeholder
        first_image = ProductImage.query.filter_by(product_id=self.id).first()
        if first_image:
            return first_image.image_url
        return '/static/images/product-placeholder.jpg'
    
    @property
    def is_in_stock(self):
        return self.stock_quantity > 0
    
    def decrease_stock(self, quantity):
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            return True
        return False
    
    def increase_stock(self, quantity):
        self.stock_quantity += quantity
    
    def __repr__(self):
        return f'<Product {self.part_number}>'

class ProductImage(db.Model):
    """Product image model"""
    __tablename__ = 'product_images'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    image_url = db.Column(db.String(255), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ProductImage {self.id}>'

class Address(db.Model):
    """User address model"""
    __tablename__ = 'addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address_line1 = db.Column(db.String(255), nullable=False)
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), default='India')
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='address', lazy=True)
    
    def __repr__(self):
        return f'<Address {self.id} - {self.city}>'

class Cart(db.Model):
    """Shopping cart model"""
    __tablename__ = 'cart'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='unique_cart_item'),
    )
    
    @property
    def total_price(self):
        return self.product.discounted_price * self.quantity
    
    def __repr__(self):
        return f'<Cart {self.id}>'

class Order(db.Model):
    """Order model"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    tax_amount = db.Column(db.Numeric(10, 2), default=0)
    shipping_amount = db.Column(db.Numeric(10, 2), default=0)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(20), default='cod')
    payment_status = db.Column(db.String(20), default='pending')
    order_status = db.Column(db.String(20), default='pending')
    tracking_number = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')
    status_history = db.relationship('OrderStatusHistory', backref='order', lazy=True, cascade='all, delete-orphan')
    
    @staticmethod
    def generate_order_number():
        import random
        import string
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f'ASH-{timestamp}-{random_str}'
    
    def update_status(self, new_status, notes=None):
        from app import create_app
        app = create_app()
        
        with app.app_context():
            self.order_status = new_status
            history = OrderStatusHistory(
                order_id=self.id,
                status=new_status,
                notes=notes
            )
            db.session.add(history)
            db.session.commit()
    
    def get_status_timeline(self):
        timeline = []
        for history in self.status_history:
            timeline.append({
                'status': history.status,
                'timestamp': history.created_at,
                'notes': history.notes
            })
        return sorted(timeline, key=lambda x: x['timestamp'])
    
    def __repr__(self):
        return f'<Order {self.order_number}>'

class OrderItem(db.Model):
    """Order item model"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    part_number = db.Column(db.String(50), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    def __repr__(self):
        return f'<OrderItem {self.id}>'

class OrderStatusHistory(db.Model):
    """Order status history model"""
    __tablename__ = 'order_status_history'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<OrderStatusHistory {self.id}>'

class PushSubscription(db.Model):
    """Push notification subscription model"""
    __tablename__ = 'push_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    endpoint = db.Column(db.Text, nullable=False)
    p256dh = db.Column(db.String(255), nullable=False)
    auth = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<PushSubscription {self.id}>'

class Wishlist(db.Model):
    """Wishlist model"""
    __tablename__ = 'wishlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'product_id', name='unique_wishlist_item'),
    )
    
    def __repr__(self):
        return f'<Wishlist {self.id}>'

class Review(db.Model):
    """Product review model"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Review {self.id}>'
        
class OTPVerification(db.Model):
    """OTP verification model"""
    __tablename__ = 'otp_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    contact_info = db.Column(db.String(100), nullable=False, index=True)  # Email or phone
    otp_code = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(50), nullable=False)  # 'login', 'registration', 'password_reset'
    expires_at = db.Column(db.DateTime, nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_valid(self):
        return datetime.utcnow() < self.expires_at and not self.is_used
    
    @staticmethod
    def generate_otp(contact_info, purpose, expiration_minutes=2):
        import secrets
        otp_code = ''.join(secrets.choice('0123456789') for _ in range(6))
        expires_at = datetime.utcnow() + timedelta(minutes=expiration_minutes)
        
        # Invalidate old OTPs for this contact and purpose
        OTPVerification.query.filter_by(
            contact_info=contact_info, 
            purpose=purpose, 
            is_used=False
        ).update({'is_used': True})
        
        new_otp = OTPVerification(
            contact_info=contact_info,
            otp_code=otp_code,
            purpose=purpose,
            expires_at=expires_at
        )
        db.session.add(new_otp)
        db.session.commit()
        return otp_code
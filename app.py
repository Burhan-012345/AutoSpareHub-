#!/usr/bin/env python3
"""
AutoSpareHub - Spare Parts E-Commerce Application
Main application file
"""

import os
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_migrate import Migrate
from config import Config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
mail = Mail()
migrate = Migrate()

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Import models
    from models import User, Product, Category, Cart, Order
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.shop import shop_bp
    from routes.cart import cart_bp
    from routes.admin import admin_bp
    from routes.user import user_bp
    from routes.notifications import notifications_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(shop_bp, url_prefix='/shop')
    app.register_blueprint(cart_bp, url_prefix='/cart')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    
    # Main routes
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/about')
    def about():
        return render_template('about.html')
    
    @app.route('/contact')
    def contact():
        return render_template('contact.html')
    
    @app.route('/manifest.json')
    def manifest():
        return app.send_static_file('manifest.json')
    
    @app.route('/service-worker.js')
    def service_worker():
        return app.send_static_file('service-worker.js')
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    # Create tables
    with app.app_context():
        db.create_all()
        
        # Create admin user if not exists
        from werkzeug.security import generate_password_hash
        admin_email = app.config.get('ADMIN_EMAIL', 'admin@autosparehub.com')
        admin_exists = User.query.filter_by(email=admin_email).first()
        
        if not admin_exists:
            admin_user = User(
                name='Administrator',
                email=admin_email,
                password=generate_password_hash('Admin@123'),
                role='admin',
                email_verified=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"Admin user created: {admin_email}")
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
"""
Configuration settings for AutoSpareHub
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'auto01-burhan-secret-key-2024'
    
    # Database - PythonAnywhere MySQL
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://auto01:Burhan@01@auto01.mysql.pythonanywhere-services.com/auto01$default'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_POOL_RECYCLE = 299  # PythonAnywhere specific
    SQLALCHEMY_POOL_TIMEOUT = 20
    
    # Email Configuration (Gmail)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'ahmedburhan4834@gmail.com'
    MAIL_PASSWORD = 'iwrbpwdenrqdgmcl'
    MAIL_DEFAULT_SENDER = ('AutoSpareHub', 'ahmedburhan4834@gmail.com')
    
    # Admin
    ADMIN_EMAIL = 'ahmedburhan4834@gmail.com'
    
    # PWA Push Notifications (VAPID)
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', 'your-vapid-public-key')
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', 'your-vapid-private-key')
    VAPID_CLAIM_EMAIL = 'mailto:ahmedburhan4834@gmail.com'
    
    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    
    # Security
    SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT') or 'auto01-password-salt-secure'
    
    # File upload
    UPLOAD_FOLDER = 'static/images/products'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Application
    APP_NAME = 'AutoSpareHub'
    APP_URL = os.environ.get('APP_URL', 'https://auto01.pythonanywhere.com')
    
    # Currency
    CURRENCY = '₹'
    TAX_RATE = 0.18  # 18% GST
    SHIPPING_RATE = 50.00  # Fixed shipping for now

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    APP_URL = 'http://localhost:5000'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Requires HTTPS

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
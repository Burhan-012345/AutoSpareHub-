"""
Authentication routes for AutoSpareHub
"""

import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
from app import db, mail
from models import User, PasswordResetToken
from forms import RegistrationForm, LoginForm, ForgotPasswordForm, ResetPasswordForm
from flask_mail import Message

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Create new user
        user = User(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            password=form.password.data
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Send welcome email
        send_welcome_email(user)
        
        # Auto login after registration
        login_user(user, remember=True)
        
        flash('Registration successful! Welcome to AutoSpareHub.', 'success')
        return redirect(url_for('index'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and user.verify_password(form.password.data):
            login_user(user, remember=form.remember.data)
            
            # Redirect to next page if exists
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            
            flash('Login successful!', 'success')
            return redirect(next_page)
        else:
            flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password request"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = ForgotPasswordForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # Generate reset token
            token = PasswordResetToken.create_token(user.id)
            
            # Send reset email
            send_password_reset_email(user, token)
        
        # Show success message even if email doesn't exist (security)
        flash('If your email is registered, you will receive a password reset link shortly.', 'info')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/forgot_password.html', form=form)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Validate token
    reset_token = PasswordResetToken.query.filter_by(token=token, used=False).first()
    
    if not reset_token or not reset_token.is_valid():
        flash('Invalid or expired reset token.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.get(reset_token.user_id)
    if not user:
        flash('Invalid user.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        # Update password
        user.password = form.password.data
        
        # Mark token as used
        reset_token.used = True
        
        db.session.commit()
        
        flash('Your password has been reset. Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('user/profile.html')

# Email Functions
def send_welcome_email(user):
    """Send welcome email to new user"""
    try:
        msg = Message(
            subject='Welcome to AutoSpareHub!',
            recipients=[user.email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.html = render_template(
            'email/welcome.html',
            user=user,
            app_name=current_app.config['APP_NAME']
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send welcome email: {e}')
        return False

def send_password_reset_email(user, token):
    """Send password reset email"""
    try:
        reset_url = url_for('auth.reset_password', token=token, _external=True)
        
        msg = Message(
            subject='Reset Your AutoSpareHub Password',
            recipients=[user.email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.html = render_template(
            'email/password_reset.html',
            user=user,
            reset_url=reset_url,
            app_name=current_app.config['APP_NAME'],
            expiry_hours=1  # Token expires in 1 hour
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send password reset email: {e}')
        return False
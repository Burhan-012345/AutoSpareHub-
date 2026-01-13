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
from forms import OTPVerificationForm
from models import OTPVerification

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
    """User login with OTP"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # Send OTP
            otp_code = OTPVerification.generate_otp(form.email.data, 'login')
            send_otp_email(form.email.data, otp_code)
            
            # Redirect to OTP verification
            session['otp_contact'] = form.email.data
            session['otp_purpose'] = 'login'
            
            flash('OTP sent to your email. Please verify.', 'info')
            return redirect(url_for('auth.verify_otp', 
                                  contact=form.email.data, 
                                  purpose='login'))
        else:
            flash('User not found.', 'danger')
    
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
        
@auth_bp.route('/send-otp', methods=['POST'])
def send_otp():
    """Send OTP to user"""
    if current_user.is_authenticated:
        return jsonify({'success': False, 'message': 'Already authenticated'})
    
    data = request.get_json()
    contact_info = data.get('contact')
    purpose = data.get('purpose', 'login')
    
    if not contact_info:
        return jsonify({'success': False, 'message': 'Contact info required'})
    
    # Generate and send OTP
    otp_code = OTPVerification.generate_otp(contact_info, purpose)
    
    # TODO: Send OTP via email/SMS
    # For email:
    send_otp_email(contact_info, otp_code)
    # For SMS:
    # send_otp_sms(contact_info, otp_code)
    
    return jsonify({'success': True, 'message': 'OTP sent successfully'})

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    """Verify OTP"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = OTPVerificationForm()
    
    # Get contact info from session or query params
    contact_info = request.args.get('contact') or session.get('otp_contact')
    purpose = request.args.get('purpose', 'login') or session.get('otp_purpose')
    
    if not contact_info:
        flash('Invalid verification request.', 'danger')
        return redirect(url_for('auth.login'))
    
    if form.validate_on_submit():
        # Verify OTP
        otp_record = OTPVerification.query.filter_by(
            contact_info=contact_info,
            otp_code=form.otp.data,
            purpose=purpose,
            is_used=False
        ).first()
        
        if not otp_record:
            flash('Invalid OTP code.', 'danger')
            return render_template('auth/verify_otp.html', 
                                 form=form, 
                                 contact_info=contact_info,
                                 purpose=purpose)
        
        if not otp_record.is_valid():
            flash('OTP has expired.', 'danger')
            return render_template('auth/verify_otp.html', 
                                 form=form, 
                                 contact_info=contact_info,
                                 purpose=purpose)
        
        # Mark OTP as used
        otp_record.is_used = True
        db.session.commit()
        
        # Handle based on purpose
        if purpose == 'login':
            # Find user and login
            user = User.query.filter_by(email=contact_info).first()
            if user:
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
        
        elif purpose == 'registration':
            # Redirect to registration with verified email
            session['verified_email'] = contact_info
            return redirect(url_for('auth.register'))
        
        elif purpose == 'password_reset':
            # Redirect to password reset
            session['reset_email'] = contact_info
            return redirect(url_for('auth.reset_password'))
    
    return render_template('auth/verify_otp.html', 
                         form=form, 
                         contact_info=contact_info,
                         purpose=purpose)

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    """Resend OTP"""
    data = request.get_json()
    contact_info = data.get('contact')
    purpose = data.get('purpose', 'login')
    
    if not contact_info:
        return jsonify({'success': False, 'message': 'Contact info required'})
    
    # Generate new OTP
    otp_code = OTPVerification.generate_otp(contact_info, purpose)
    
    # Send OTP
    send_otp_email(contact_info, otp_code)
    
    return jsonify({'success': True, 'message': 'OTP resent successfully'})

def send_otp_email(email, otp_code):
    """Send OTP via email"""
    try:
        msg = Message(
            subject='Your AutoSpareHub Verification Code',
            recipients=[email],
            sender=current_app.config['MAIL_DEFAULT_SENDER']
        )
        
        msg.html = render_template(
            'email/otp_verification.html',
            otp_code=otp_code,
            app_name=current_app.config['APP_NAME'],
            expiry_minutes=2
        )
        
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f'Failed to send OTP email: {e}')
        return False
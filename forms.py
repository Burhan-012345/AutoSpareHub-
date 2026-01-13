"""
Forms for AutoSpareHub
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, \
    TextAreaField, DecimalField, IntegerField, RadioField, HiddenField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, Optional, NumberRange
from models import User

class RegistrationForm(FlaskForm):
    """User registration form"""
    name = StringField('Full Name', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    agree_terms = BooleanField('I agree to the Terms and Conditions', validators=[DataRequired()])
    submit = SubmitField('Sign Up')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('This email is already registered. Please use a different email.')

class LoginForm(FlaskForm):
    """User login form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class ForgotPasswordForm(FlaskForm):
    """Forgot password form"""
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Reset Link')

class ResetPasswordForm(FlaskForm):
    """Reset password form"""
    password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')

class AddressForm(FlaskForm):
    """Address form"""
    full_name = StringField('Full Name', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=10, max=15)])
    address_line1 = StringField('Address Line 1', validators=[DataRequired(), Length(max=255)])
    address_line2 = StringField('Address Line 2', validators=[Optional(), Length(max=255)])
    city = StringField('City', validators=[DataRequired(), Length(max=100)])
    state = StringField('State', validators=[DataRequired(), Length(max=100)])
    postal_code = StringField('Postal Code', validators=[DataRequired(), Length(max=20)])
    country = StringField('Country', validators=[DataRequired(), Length(max=100)])
    is_default = BooleanField('Set as default address')
    submit = SubmitField('Save Address')

class ProductForm(FlaskForm):
    """Product form for admin"""
    name = StringField('Product Name', validators=[DataRequired(), Length(max=200)])
    part_number = StringField('Part Number', validators=[DataRequired(), Length(max=50)])
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    brand_id = SelectField('Vehicle Brand', coerce=int, validators=[Optional()])
    model_id = SelectField('Vehicle Model', coerce=int, validators=[Optional()])
    manufacturing_year = StringField('Manufacturing Year', validators=[Optional(), Length(max=20)])
    price = DecimalField('Price', validators=[DataRequired(), NumberRange(min=0)])
    discount = DecimalField('Discount (%)', validators=[Optional(), NumberRange(min=0, max=100)], default=0)
    stock_quantity = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])
    description = TextAreaField('Description', validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    images = FileField('Product Images', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    submit = SubmitField('Save Product')

class SearchForm(FlaskForm):
    """Search form"""
    query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

class CheckoutForm(FlaskForm):
    """Checkout form"""
    address_id = RadioField('Select Address', coerce=int, validators=[DataRequired()])
    payment_method = RadioField('Payment Method', 
                               choices=[('cod', 'Cash on Delivery'), ('online', 'Online Payment')],
                               default='cod',
                               validators=[DataRequired()])
    notes = TextAreaField('Order Notes (Optional)')
    agree_terms = BooleanField('I agree to the Terms and Conditions', validators=[DataRequired()])
    submit = SubmitField('Place Order')

class CategoryForm(FlaskForm):
    """Category form"""
    name = StringField('Category Name', validators=[DataRequired(), Length(max=100)])
    slug = StringField('Slug', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Optional()])
    parent_id = SelectField('Parent Category', coerce=int, validators=[Optional()])
    submit = SubmitField('Save Category')

class VehicleBrandForm(FlaskForm):
    """Vehicle brand form"""
    name = StringField('Brand Name', validators=[DataRequired(), Length(max=50)])
    logo = FileField('Logo', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Images only!')
    ])
    submit = SubmitField('Save Brand')

class VehicleModelForm(FlaskForm):
    """Vehicle model form"""
    brand_id = SelectField('Brand', coerce=int, validators=[DataRequired()])
    name = StringField('Model Name', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Save Model')
    
class OTPVerificationForm(FlaskForm):
    """OTP verification form"""
    otp = StringField('OTP Code', validators=[
        DataRequired(),
        Length(min=6, max=6, message='OTP must be 6 digits'),
        Regexp('^[0-9]*$', message='OTP must contain only numbers')
    ])
    submit = SubmitField('Verify OTP')
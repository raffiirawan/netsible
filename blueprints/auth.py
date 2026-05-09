from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User
from extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication handler."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if user and user.check_password(password):
            login_user(user)
            flash('Login berhasil!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('Username/email atau password salah.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout the current user."""
    logout_user()
    flash('Anda telah logout.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page."""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        # Always show success message to prevent email enumeration
        flash('Jika email terdaftar, tautan pemulihan telah dikirim.', 'info')
        return redirect(url_for('auth.forgot_password'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    return render_template('netsible_profile_page.html')

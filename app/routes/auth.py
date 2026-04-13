# app/routes/auth.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required
from app.models import User
from app.forms import RegistrationForm, LoginForm
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils import generate_otp
from app.email import send_otp_email
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

# ✅ /register route for Students and CRs only
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()

    # ❌ Prevent admin from registering via student route
    if request.method == 'POST' and form.role.data == 'admin':
        flash('Admin registration is not allowed here. Use the dedicated admin registration page.', 'danger')
        return redirect(url_for('auth.register'))

    if form.validate_on_submit():

        existing_user = User.query.filter(User.email == form.email.data).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register'))

        # ✅ Check roll number uniqueness
        existing_roll = User.query.filter_by(roll_no=form.roll_no.data).first()
        if existing_roll:
            flash('Roll number already registered.', 'danger')
            return redirect(url_for('auth.register'))

        # ✅ Limit CRs to 2 per branch + semester
        if form.role.data == 'cr':
            cr_count = User.query.filter_by(
                role='cr',
                branch=form.branch.data,
                semester=form.semester.data
            ).count()

            if cr_count >= 2:
                flash(f'Only 2 CRs allowed for {form.branch.data} - Semester {form.semester.data}.', 'danger')
                return redirect(url_for('auth.register'))

        # 🔹 Generate OTP
        otp = generate_otp()

        # 🔹 Store form data temporarily in session
        session['register_data'] = {
            "name": form.name.data,
            "roll_no": form.roll_no.data,
            "email": form.email.data,
            "password": generate_password_hash(form.password.data),
            "role": form.role.data,
            "branch": form.branch.data,
            "semester": form.semester.data,
            "otp": otp,
            "otp_time": datetime.utcnow().isoformat()
        }

        # 🔹 Send OTP Email
        send_otp_email(form.email.data, otp)

        flash('OTP sent to your email. Please verify.', 'info')
        return redirect(url_for('auth.verify_email'))

    return render_template('register.html', form=form)


# ✅ Email Verification Route
@auth_bp.route('/verify-email', methods=['GET', 'POST'])
def verify_email():

    if 'register_data' not in session:
        return redirect(url_for('auth.register'))

    if request.method == 'POST':

        entered_otp = request.form.get("otp")
        data = session['register_data']

        real_otp = data['otp']
        otp_time = datetime.fromisoformat(data['otp_time'])

        # 🔒 OTP Expiry Check (5 minutes)
        if datetime.utcnow() > otp_time + timedelta(minutes=5):
            session.pop('register_data')
            flash("OTP expired. Please register again.", "danger")
            return redirect(url_for('auth.register'))

        if entered_otp == real_otp:

            # ✅ Check roll number again (safety)
            existing_roll = User.query.filter_by(roll_no=data['roll_no']).first()
            if existing_roll:
                flash('Roll number already registered.', 'danger')
                return redirect(url_for('auth.register'))

            new_user = User(
                name=data['name'],
                roll_no=data['roll_no'],
                email=data['email'],
                password=data['password'],
                role=data['role'],
                branch=data['branch'],
                semester=data['semester']
            )

            db.session.add(new_user)
            db.session.commit()

            session.pop('register_data')

            flash('Account created successfully!', 'success')
            return redirect(url_for('auth.login'))

        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('verify_email.html')


@auth_bp.route('/resend-otp')
def resend_otp():

    if 'register_data' not in session:
        return redirect(url_for('auth.register'))

    data = session['register_data']

    # generate new OTP
    otp = generate_otp()

    # update session
    session['register_data']['otp'] = otp
    session['register_data']['otp_time'] = datetime.utcnow().isoformat()

    # send email again
    send_otp_email(data['email'], otp)

    flash("A new OTP has been sent to your email.", "info")

    return redirect(url_for('auth.verify_email'))


# ✅ Admin registration route with limit and unique branch constraint
@auth_bp.route('/register_admin', methods=['GET', 'POST'])
def register_admin():
    form = RegistrationForm()
    form.role.data = 'admin'
    form.role.render_kw = {'readonly': True}

    admin_count = User.query.filter_by(role='admin').count()
    existing_admin_branches = [u.branch for u in User.query.filter_by(role='admin').all()]

    if request.method == 'POST':

        if admin_count >= 6:
            flash('Maximum of 6 admins allowed. Registration denied.', 'danger')
            return redirect(url_for('auth.register_admin'))

        if form.branch.data in existing_admin_branches:
            flash(f"An admin from branch '{form.branch.data}' already exists. Choose a different branch.", 'danger')
            return redirect(url_for('auth.register_admin'))

        existing_user = User.query.filter(User.email == form.email.data).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return redirect(url_for('auth.register_admin'))

        hashed_password = generate_password_hash(form.password.data)

        admin_user = User(
            name=form.name.data,
            roll_no=None,
            email=form.email.data,
            password=hashed_password,
            role='admin',
            branch=form.branch.data,
            semester=None
        )

        db.session.add(admin_user)
        db.session.commit()

        flash('Admin account created successfully!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register_admin.html', form=form, admin_count=admin_count)


# ✅ Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f'Welcome, {user.name}!', 'success')
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html', form=form)


# ✅ Logout route
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/forgot-password', methods=['GET','POST'])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email")

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("Email not registered", "danger")
            return redirect(url_for('auth.forgot_password'))

        otp = generate_otp()

        session['reset_data'] = {
            "email": email,
            "otp": otp,
            "otp_time": datetime.utcnow().isoformat()
        }

        send_otp_email(email, otp, "reset")

        flash("OTP sent to your email.", "info")

        return redirect(url_for('auth.verify_reset_otp'))

    return render_template("forgot_password.html")

@auth_bp.route('/resend-reset-otp')
def resend_reset_otp():

    if 'reset_data' not in session:
        return redirect(url_for('auth.forgot_password'))

    data = session['reset_data']

    # generate new OTP
    otp = generate_otp()

    # update session
    session['reset_data']['otp'] = otp
    session['reset_data']['otp_time'] = datetime.utcnow().isoformat()

    # send email again
    send_otp_email(data['email'], otp, "reset")

    flash("A new OTP has been sent to your email.", "info")

    return redirect(url_for('auth.verify_reset_otp'))

@auth_bp.route('/verify-reset-otp', methods=['GET','POST'])
def verify_reset_otp():

    if 'reset_data' not in session:
        return redirect(url_for('auth.forgot_password'))

    if request.method == "POST":

        entered_otp = request.form.get("otp")
        data = session['reset_data']

        real_otp = data['otp']
        otp_time = datetime.fromisoformat(data['otp_time'])

        # 🔒 OTP Expiry Check
        if datetime.utcnow() > otp_time + timedelta(minutes=5):
            session.pop('reset_data')
            flash("OTP expired. Request again.", "danger")
            return redirect(url_for('auth.forgot_password'))

        if entered_otp == real_otp:

            flash("OTP verified. Set new password.", "success")
            return redirect(url_for('auth.reset_password'))

        else:
            flash("Invalid OTP", "danger")

    return render_template("verify_reset_otp.html")


@auth_bp.route('/reset-password', methods=['GET','POST'])
def reset_password():

    if 'reset_data' not in session:
        return redirect(url_for('auth.forgot_password'))

    if request.method == "POST":

        new_password = request.form.get("password")

        user = User.query.filter_by(email=session['reset_data']['email']).first()

        user.password = generate_password_hash(new_password)

        db.session.commit()

        session.pop('reset_data')

        flash("Password reset successfully. Please login.", "success")

        return redirect(url_for('auth.login'))

    return render_template("reset_password.html")


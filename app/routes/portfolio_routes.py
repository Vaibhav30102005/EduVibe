import uuid
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import Portfolio, User, db

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/portfolio')

# ---------------------------
# 🔹 View Own Portfolio
# ---------------------------
@portfolio_bp.route('/')
@login_required
def view_portfolio():
    portfolio = Portfolio.query.filter_by(student_id=current_user.id).first()
    return render_template('portfolio/view.html', portfolio=portfolio)


# ---------------------------
# 🔹 Edit Own Portfolio
# ---------------------------
@portfolio_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit_portfolio():
    portfolio = Portfolio.query.filter_by(student_id=current_user.id).first()
    if not portfolio:
        portfolio = Portfolio(student_id=current_user.id)

    if request.method == 'POST':
        # Text Fields
        portfolio.achievements = request.form.get('achievements')
        portfolio.skills = request.form.get('skills')
        portfolio.interests = request.form.get('interests')
        portfolio.github_link = request.form.get('github_link') or None
        portfolio.linkedin_link = request.form.get('linkedin_link') or None

        # Upload Directory
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'portfolio')
        os.makedirs(upload_folder, exist_ok=True)

        # Handle File Uploads
        for field in ['profile_pic', 'resume', 'certificates']:
            file = request.files.get(field)
            if file and file.filename:
                ext = file.filename.rsplit('.', 1)[-1].lower()
                if ext in current_app.config.get('ALLOWED_EXTENSIONS', set(['pdf', 'jpg', 'jpeg', 'png'])):
                    filename = secure_filename(f"{current_user.id}_{uuid.uuid4().hex}_{file.filename}")
                    file_path = os.path.join(upload_folder, filename)
                    file.save(file_path)
                    setattr(portfolio, field, f'uploads/portfolio/{filename}')
                else:
                    flash(f"Invalid file type for {field}", "danger")
                    return redirect(request.url)

        db.session.add(portfolio)
        db.session.commit()
        flash("Portfolio updated successfully ✅", "success")
        return redirect(url_for('portfolio.view_portfolio'))

    return render_template('portfolio/edit.html', portfolio=portfolio)


# ---------------------------
# 🔹 Admin View All Portfolios
# ---------------------------
@portfolio_bp.route('/admin-view')
@login_required
def admin_view():
    if current_user.role != 'admin':
        flash("Access denied 🚫", "danger")
        return redirect(url_for('dashboard.index'))

    branch = request.args.get('branch')
    semester = request.args.get('semester')

    query = Portfolio.query.join(User, Portfolio.student_id == User.id).filter(User.role.in_(['student', 'cr']))

    if branch:
        query = query.filter(User.branch == branch)
    if semester:
        query = query.filter(User.semester == semester)

    portfolios = query.all()

    all_branches = db.session.query(User.branch).distinct().all()
    all_semesters = db.session.query(User.semester).distinct().all()

    return render_template(
        'portfolio/admin_view.html',
        portfolios=portfolios,
        selected_branch=branch,
        selected_semester=semester,
        all_branches=[b[0] for b in all_branches if b[0]],
        all_semesters=[s[0] for s in all_semesters if s[0]]
    )


# ---------------------------
# 🔹 Upload Single File (Optional route)
# ---------------------------
@portfolio_bp.route('/upload', methods=['POST'])
@login_required
def upload_file():
    file = request.files.get('file')
    if not file or file.filename.strip() == '':
        flash('No file selected ❌', 'warning')
        return redirect(request.referrer or url_for('portfolio.view_portfolio'))

    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in current_app.config.get('ALLOWED_EXTENSIONS', set(['pdf', 'jpg', 'jpeg', 'png'])):
        flash('Invalid file type ❌ Allowed: .pdf, .jpg, .png', 'danger')
        return redirect(request.referrer or url_for('portfolio.view_portfolio'))

    filename = secure_filename(f"{current_user.id}_{uuid.uuid4().hex}_{file.filename}")
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'portfolio')
    os.makedirs(upload_folder, exist_ok=True)

    file.save(os.path.join(upload_folder, filename))
    flash('File uploaded successfully ✅', 'success')
    return redirect(url_for('portfolio.view_portfolio'))

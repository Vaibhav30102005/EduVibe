from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from app.models import User
from app import db

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.route('/manage-users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        return redirect(url_for('dashboard.index'))

    # ✅ Read filter parameters from request.args
    selected_role = request.args.get('role')
    selected_branch = request.args.get('branch')
    selected_semester = request.args.get('semester')

    # ✅ Base query
    users_query = User.query

    # ✅ Apply filters only if selected
    if selected_role:
        users_query = users_query.filter_by(role=selected_role)
    if selected_branch:
        users_query = users_query.filter_by(branch=selected_branch)
    if selected_semester:
        users_query = users_query.filter_by(semester=selected_semester)

    users = users_query.order_by(User.role, User.branch, User.semester, User.name).all()

    # ✅ Dropdown options (pre-fill with distinct values)
    roles = ['student', 'cr']
    branches = [b[0] for b in db.session.query(User.branch).filter(User.branch != None).distinct().all()]
    semesters = [s[0] for s in db.session.query(User.semester).filter(User.semester != None).distinct().all()]

    return render_template(
        'admin/manage_users.html',
        users=users,
        roles=roles,
        branches=branches,
        semesters=semesters,
        selected_role=selected_role,
        selected_branch=selected_branch,
        selected_semester=selected_semester,
        user=current_user
    )

@bp.route('/delete-user/<int:user_id>')
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return redirect(url_for('dashboard.index'))

    user = User.query.get_or_404(user_id)

    if user.role == 'admin':
        return "Cannot delete an admin user!", 403

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('admin.manage_users'))

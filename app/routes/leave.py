from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
from app import db
from app.models import LeaveApplication, User, ist_now
from app.forms.leave_forms import LeaveApplicationForm, ApproveLeaveForm
from datetime import date

leave_bp = Blueprint('leave', __name__, url_prefix='/leave')

# -------------------------
# 🔹 Apply for Leave
# -------------------------
@leave_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply_leave():
    form = LeaveApplicationForm()

    if form.validate_on_submit():
        # ✅ Extra backend validation for date fields
        if form.from_date.data < date.today():
            flash("From Date cannot be in the past ⚠️", "danger")
            return render_template('leave/apply.html', form=form)

        if form.to_date.data < date.today():
            flash("To Date cannot be in the past ⚠️", "danger")
            return render_template('leave/apply.html', form=form)

        if form.to_date.data < form.from_date.data:
            flash("To Date cannot be earlier than From Date ⚠️", "danger")
            return render_template('leave/apply.html', form=form)

        filename = None
        if form.document.data:
            file = form.document.data
            filename = secure_filename(file.filename)

            # Save the file to the uploads folder
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'leave_docs')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

        leave = LeaveApplication(
            user_id=current_user.id,
            reason=form.reason.data,
            from_date=form.from_date.data,   # ✅ Added
            to_date=form.to_date.data,       # ✅ Added
            file_path=filename,
            created_at=ist_now(),
            status='Pending'
        )
        db.session.add(leave)
        db.session.commit()
        flash("Leave application submitted successfully ✅", "success")
        return redirect(url_for('leave.view_my_leaves'))

    return render_template('leave/apply.html', form=form)


# -------------------------
# 🔹 View My Leave Applications
# -------------------------
@leave_bp.route('/my')
@login_required
def view_my_leaves():
    leaves = LeaveApplication.query.filter_by(user_id=current_user.id) \
        .order_by(LeaveApplication.created_at.desc()).all()
    return render_template('leave/my_applications.html', leaves=leaves)


# -------------------------
# 🔹 Edit My Leave Application
# -------------------------
@leave_bp.route('/edit/<int:leave_id>', methods=['GET', 'POST'])
@login_required
def edit_leave(leave_id):
    leave = LeaveApplication.query.get_or_404(leave_id)

    # Only the owner can edit & only if status is pending
    if leave.user_id != current_user.id:
        abort(403)
    if leave.status != 'Pending':
        flash("You can only edit pending leave applications ⚠️", "warning")
        return redirect(url_for('leave.view_my_leaves'))

    form = LeaveApplicationForm(obj=leave)

    if form.validate_on_submit():
        # ✅ Extra backend validation for date fields
        if form.from_date.data < date.today():
            flash("From Date cannot be earlier than From Date ⚠️", "danger")
            return render_template('leave/edit.html', form=form, leave=leave)

        if form.to_date.data < date.today():
            flash("To Date cannot be earlier than From Date ⚠️", "danger")
            return render_template('leave/edit.html', form=form, leave=leave)

        if form.to_date.data < form.from_date.data:
            flash("To Date cannot be earlier than From Date ⚠️", "danger")
            return render_template('leave/edit.html', form=form, leave=leave)

        leave.reason = form.reason.data
        leave.from_date = form.from_date.data   # ✅ Added
        leave.to_date = form.to_date.data       # ✅ Added

        if form.document.data:
            file = form.document.data
            filename = secure_filename(file.filename)
            upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'leave_docs')
            os.makedirs(upload_folder, exist_ok=True)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            leave.file_path = filename

        db.session.commit()
        flash("Leave updated successfully ✅", "success")
        return redirect(url_for('leave.view_my_leaves'))

    return render_template('leave/edit.html', form=form, leave=leave)


# -------------------------
# 🔹 Delete My Leave Application
# -------------------------
@leave_bp.route('/delete/<int:leave_id>', methods=['POST'])
@login_required
def delete_leave(leave_id):
    leave = LeaveApplication.query.get_or_404(leave_id)

    # Only the owner can delete & only if status is pending
    if leave.user_id != current_user.id:
        abort(403)
    if leave.status != 'Pending':
        flash("You can only delete pending leave applications ⚠️", "warning")
        return redirect(url_for('leave.view_my_leaves'))

    db.session.delete(leave)
    db.session.commit()
    flash("Leave deleted successfully 🗑️", "success")
    return redirect(url_for('leave.view_my_leaves'))


# -------------------------
# 🔹 Admin View of Branch-Specific Leaves (Students + CRs)
# -------------------------
@leave_bp.route('/admin')
@login_required
def view_all_leaves():
    if current_user.role != 'admin':
        flash("Access denied 🚫", "danger")
        return redirect(url_for('dashboard.index'))

    # ✅ Fetch Students + CRs of the same branch
    user_ids = db.session.query(User.id).filter(
        User.branch == current_user.branch,
        User.role.in_(["student", "cr"])   # 👈 Lowercase 'cr' used
    ).subquery()

    leaves = LeaveApplication.query.filter(
        LeaveApplication.user_id.in_(user_ids)
    ).order_by(LeaveApplication.created_at.desc()).all()

    return render_template('leave/view_admin.html', leaves=leaves)


# -------------------------
# 🔹 Approve or Reject Leave
# -------------------------
@leave_bp.route('/approve/<int:leave_id>', methods=['GET', 'POST'])
@login_required
def approve_leave(leave_id):
    if current_user.role != 'admin':
        flash("Access denied 🚫", "danger")
        return redirect(url_for('dashboard.index'))

    leave = LeaveApplication.query.get_or_404(leave_id)
    student = User.query.get(leave.user_id)

    # 🔒 Only same branch admin can take action
    if not student or student.branch != current_user.branch:
        flash("You are not authorized to approve this leave ⚠️", "danger")
        return redirect(url_for('leave.view_all_leaves'))

    form = ApproveLeaveForm(status=leave.status)

    if form.validate_on_submit():
        leave.status = form.status.data
        db.session.commit()
        flash("Leave status updated ✅", "success")
        return redirect(url_for('leave.view_all_leaves'))

    return render_template('leave/approve.html', leave=leave, form=form)


# -------------------------
# 🔹 Download Uploaded Document
# -------------------------
@leave_bp.route('/download/<filename>')
@login_required
def download_file(filename):
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'leave_docs')
    return send_from_directory(upload_folder, filename, as_attachment=True)


# -------------------------
# 🔹 View Uploaded Document
# -------------------------
@leave_bp.route('/view/<filename>')
@login_required
def view_file(filename):
    upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'leave_docs')
    return send_from_directory(
        directory=upload_folder,
        path=filename,
        mimetype='application/pdf',
        as_attachment=False
    )

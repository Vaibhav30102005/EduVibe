from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app.models import db, Complaint, User  # adjust import path as needed

# 🔹 Correct blueprint name is 'complaint' (NOT 'complaints')
complaint_bp = Blueprint('complaint', __name__, url_prefix='/complaint')

# -------------------------
# 🔹 Submit Complaint
# -------------------------
@complaint_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_complaint():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        visibility = request.form.get('visibility', 'cr_admin')  # ✅ Default: cr_admin

        complaint = Complaint(
            title=title,
            description=description,
            student_id=current_user.id,
            visibility=visibility   # ✅ Save visibility
        )
        db.session.add(complaint)
        db.session.commit()
        flash("Complaint submitted successfully.", "success")
        return redirect(url_for('complaint.view_my_complaints'))
    return render_template('complaint/submit_complaint.html')

# -------------------------
# 🔹 View All Complaints
# -------------------------
@complaint_bp.route('/all')
@login_required
def all_complaints():
    if current_user.role == 'admin':
        # ✅ Admin sees everything
        complaints = Complaint.query.join(User, Complaint.student).filter(
            User.branch == current_user.branch
        ).order_by(Complaint.timestamp.desc()).all()

    elif current_user.role == 'cr':
        # ✅ CRs see only CR+Admin complaints
        complaints = Complaint.query.join(User, Complaint.student).filter(
            User.branch == current_user.branch,
            User.semester == current_user.semester,
            Complaint.visibility == 'cr_admin'
        ).order_by(Complaint.timestamp.desc()).all()

    else:
        flash("Access denied", "danger")
        return redirect(url_for('dashboard.index'))

    return render_template('complaint/all_complaints.html', complaints=complaints)


# -------------------------
# 🔹 Resolve Complaint
# -------------------------
@complaint_bp.route('/resolve/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def resolve_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    student = User.query.get(complaint.student_id)

    if current_user.role == 'admin':
        if student.branch != current_user.branch:
            flash("You can only resolve complaints from your branch.", "danger")
            return redirect(url_for('complaint.all_complaints'))

    elif current_user.role == 'cr':
        # ✅ CR cannot resolve admin-only complaints
        if student.branch != current_user.branch or student.semester != current_user.semester or complaint.visibility != 'cr_admin':
            flash("You can only resolve complaints visible to CR in your branch and semester.", "danger")
            return redirect(url_for('complaint.all_complaints'))

    else:
        flash("Access denied", "danger")
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        complaint.response = request.form['response']
        complaint.status = 'Resolved'
        complaint.resolved_by_id = current_user.id
        db.session.commit()
        flash("Complaint marked as resolved.", "success")
        return redirect(url_for('complaint.all_complaints'))

    return render_template('complaint/resolve_complaint.html', complaint=complaint)

# -------------------------
# 🔹 View My Complaints
# -------------------------
@complaint_bp.route('/my')
@login_required
def view_my_complaints():
    if current_user.role != 'student':
        flash("Only students can access their personal complaint list.", "danger")
        return redirect(url_for('dashboard.index'))

    complaints = Complaint.query.filter_by(student_id=current_user.id).order_by(Complaint.timestamp.desc()).all()
    return render_template('complaint/view_my_complaints.html', complaints=complaints)

# -------------------------
# 🔹 Edit Complaint (NEW)
# -------------------------
@complaint_bp.route('/edit/<int:complaint_id>', methods=['GET', 'POST'])
@login_required
def edit_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    # Students can only edit their own complaints if not resolved
    if complaint.student_id != current_user.id:
        flash("⛔ You are not allowed to edit this complaint.", "danger")
        return redirect(url_for('complaint.view_my_complaints'))

    if complaint.status == 'Resolved':
        flash("⚠ You cannot edit a resolved complaint.", "warning")
        return redirect(url_for('complaint.view_my_complaints'))

    if request.method == 'POST':
        complaint.title = request.form['title']
        complaint.description = request.form['description']
        complaint.visibility = request.form.get('visibility', complaint.visibility)  # ✅ Allow visibility update
        db.session.commit()
        flash("✏ Complaint updated successfully.", "success")
        return redirect(url_for('complaint.view_my_complaints'))

    return render_template('complaint/edit_complaint.html', complaint=complaint)

# -------------------------
# 🔹 Delete Complaint (NEW)
# -------------------------
@complaint_bp.route('/delete/<int:complaint_id>', methods=['POST'])
@login_required
def delete_complaint(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)

    # Only owner can delete if not resolved
    if complaint.student_id != current_user.id:
        flash("⛔ You are not allowed to delete this complaint.", "danger")
        return redirect(url_for('complaint.view_my_complaints'))

    if complaint.status == 'Resolved':
        flash("⚠ You cannot delete a resolved complaint.", "warning")
        return redirect(url_for('complaint.view_my_complaints'))

    db.session.delete(complaint)
    db.session.commit()
    flash("🗑 Complaint deleted successfully.", "info")
    return redirect(url_for('complaint.view_my_complaints'))

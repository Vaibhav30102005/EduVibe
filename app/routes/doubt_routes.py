from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models import Doubt, User

doubt_bp = Blueprint('doubt', __name__, url_prefix='/doubts')


# -----------------------------
# 🔹 Post Doubt (Student Only)
# -----------------------------
@doubt_bp.route('/post', methods=['GET', 'POST'])
@login_required
def post_doubt():
    if current_user.role != 'student':
        flash("Only students can post doubts.", "danger")
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        question = request.form.get('question')
        if question:
            new_doubt = Doubt(student_id=current_user.id, question=question)
            db.session.add(new_doubt)
            db.session.commit()
            flash("Doubt submitted successfully!", "success")
            return redirect(url_for('doubt.view_doubts'))

    return render_template('doubts/post.html')


# -----------------------------
# 🔹 View Doubts (Role-Specific)
# -----------------------------
@doubt_bp.route('/view')
@login_required
def view_doubts():
    if current_user.role == 'admin':
        doubts = (
            Doubt.query
            .join(User, Doubt.student_id == User.id)
            .filter(User.branch == current_user.branch)
            .order_by(Doubt.timestamp.desc())
            .all()
        )

    elif current_user.role == 'cr':
        doubts = (
            Doubt.query
            .join(User, Doubt.student_id == User.id)
            .filter(User.branch == current_user.branch, User.semester == current_user.semester)
            .order_by(Doubt.timestamp.desc())
            .all()
        )

    elif current_user.role == 'student':
        doubts = Doubt.query.filter_by(student_id=current_user.id).order_by(Doubt.timestamp.desc()).all()

    else:
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.index'))

    return render_template('doubts/view.html', doubts=doubts)


# -----------------------------
# 🔹 Answer Doubt (Admin or CR)
# -----------------------------
@doubt_bp.route('/answer/<int:doubt_id>', methods=['GET', 'POST'])
@login_required
def answer_doubt(doubt_id):
    doubt = Doubt.query.get_or_404(doubt_id)
    student = User.query.get_or_404(doubt.student_id)

    # 🔒 CR - same branch & semester
    if current_user.role == 'cr':
        if student.branch != current_user.branch or student.semester != current_user.semester:
            flash("Access denied.", "danger")
            return redirect(url_for('doubt.view_doubts'))

    # 🔒 Admin - only same branch
    elif current_user.role == 'admin':
        if student.branch != current_user.branch:
            flash("Access denied.", "danger")
            return redirect(url_for('doubt.view_doubts'))

    else:
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        answer = request.form.get('answer')
        if answer:
            doubt.answer = answer
            doubt.resolved_by_id = current_user.id
            db.session.commit()
            flash("Doubt answered successfully!", "success")
            return redirect(url_for('doubt.view_doubts'))

    return render_template('doubts/answer.html', doubt=doubt)


# -----------------------------
# 🔹 Update Doubt 
# - Student: apna question update kar sakta hai (jab tak answer na ho)
# - Admin/CR: sirf answer update kar sakte hai
# -----------------------------
@doubt_bp.route('/update/<int:doubt_id>', methods=['GET', 'POST'])
@login_required
def update_doubt(doubt_id):
    doubt = Doubt.query.get_or_404(doubt_id)
    student = User.query.get_or_404(doubt.student_id)

    # Student apna doubt (question) update kar sakta hai (only if unanswered)
    if current_user.role == 'student':
        if doubt.student_id != current_user.id:
            flash("You cannot edit others' doubts.", "danger")
            return redirect(url_for('doubt.view_doubts'))
        if doubt.answer:
            flash("You cannot update a doubt once it has been answered.", "warning")
            return redirect(url_for('doubt.view_doubts'))

    # CR: sirf apne branch & semester ke doubt ka answer update
    elif current_user.role == 'cr':
        if student.branch != current_user.branch or student.semester != current_user.semester:
            flash("Access denied.", "danger")
            return redirect(url_for('doubt.view_doubts'))

    # Admin: sirf apne branch ke doubt ka answer update
    elif current_user.role == 'admin':
        if student.branch != current_user.branch:
            flash("Access denied.", "danger")
            return redirect(url_for('doubt.view_doubts'))

    else:
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        if current_user.role == 'student':
            new_question = request.form.get('question')
            if new_question:
                doubt.question = new_question
        else:
            new_answer = request.form.get('answer')
            if new_answer:
                doubt.answer = new_answer
                doubt.resolved_by_id = current_user.id

        db.session.commit()
        flash("Doubt updated successfully!", "success")
        return redirect(url_for('doubt.view_doubts'))

    return render_template('doubts/update.html', doubt=doubt)


# -----------------------------
# 🔹 Delete Doubt
# - ❌ Admin/CR cannot delete
# - ✅ Only Student can delete their own doubt (if unanswered)
# -----------------------------
@doubt_bp.route('/delete/<int:doubt_id>', methods=['POST'])
@login_required
def delete_doubt(doubt_id):
    doubt = Doubt.query.get_or_404(doubt_id)

    if current_user.role != 'student':
        flash("Only students can delete their doubts.", "danger")
        return redirect(url_for('doubt.view_doubts'))

    if doubt.student_id != current_user.id:
        flash("You are not authorized to delete this doubt.", "danger")
        return redirect(url_for('doubt.view_doubts'))

    if doubt.answer:
        flash("You cannot delete a doubt once it has been answered.", "warning")
        return redirect(url_for('doubt.view_doubts'))

    db.session.delete(doubt)
    db.session.commit()
    flash("Doubt deleted successfully!", "success")
    return redirect(url_for('doubt.view_doubts'))

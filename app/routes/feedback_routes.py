from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.forms.feedback_form import FeedbackForm
from app.models import Feedback, User

feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')


@feedback_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit_feedback():
    if current_user.role != 'student':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.index'))

    form = FeedbackForm()
    if form.validate_on_submit():
        feedback = Feedback(
            student_id=current_user.id,
            course_name=form.course_name.data,
            instructor_name=form.instructor_name.data,
            rating=form.rating.data,
            comments=form.comments.data
        )
        db.session.add(feedback)
        db.session.commit()
        flash("Thank you! Your feedback has been submitted.", "success")
        return redirect(url_for('dashboard.index'))

    return render_template('feedback/submit_feedback.html', form=form)

@feedback_bp.route('/view')
@login_required
def view_feedback():
    if current_user.role not in ['admin', 'cr']:
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.index'))

    if current_user.role == 'admin':
        feedbacks = Feedback.query.join(User).order_by(Feedback.id.desc()).all()
    else:
        # CR: filter by branch and semester
        feedbacks = (
            Feedback.query
            .join(User)
            .filter(User.branch == current_user.branch, User.semester == current_user.semester)
            .order_by(Feedback.id.desc())
            .all()
        )

    return render_template('feedback/view_feedback.html', feedbacks=feedbacks)

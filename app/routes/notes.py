from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from app.models import Notes
from app.forms.notes_forms import NoteUploadForm, NoteFilterForm, DeleteNoteForm
from app import db

# -----------------------------
# 🔹 Blueprint Declaration
# -----------------------------
notes_bp = Blueprint('notes', __name__)

# -----------------------------
# 🔹 Static Filters
# -----------------------------
BRANCHES = ['CSE', 'ECE', 'ME', 'CE', 'EE', 'AU']
SEMESTERS = ['1', '2', '3', '4', '5', '6']

# -----------------------------
# 🔹 View Notes Route
# -----------------------------
@notes_bp.route('/notes', methods=['GET'], endpoint='view_notes')
@login_required
def view_notes():
    """
    Display notes based on user role.
    - Admin: Can filter by branch and semester
    - CR/Student: View notes only for their own branch & semester
    """
    form = NoteFilterForm()
    delete_form = DeleteNoteForm()
    notes = []

    if current_user.role == 'admin':
        branch = request.args.get('branch')
        semester = request.args.get('semester')
        query = Notes.query

        if branch:
            query = query.filter_by(branch=branch)
        if semester:
            query = query.filter_by(semester=semester)

        notes = query.order_by(Notes.id.desc()).all()

    elif current_user.role in ['student', 'cr']:
        notes = Notes.query.filter_by(
            branch=current_user.branch,
            semester=current_user.semester
        ).order_by(Notes.id.desc()).all()

    return render_template(
        'notes.html',
        notes=notes,
        user=current_user,
        form=form,
        delete_form=delete_form,
        branches=BRANCHES,
        semesters=SEMESTERS
    )

# -----------------------------
# 🔹 Upload Notes Route
# -----------------------------
@notes_bp.route('/notes/upload', methods=['GET', 'POST'], endpoint='upload_note')
@login_required
def upload_note():
    """
    CR and Student can upload notes for their own branch and semester.
    """
    if current_user.role not in ['student', 'cr']:
        flash("❌ Only CRs and Students are allowed to upload notes.", "danger")
        return redirect(url_for('notes.view_notes'))

    form = NoteUploadForm()

    if form.validate_on_submit():
        file = form.file.data
        filename = secure_filename(file.filename)

        # Absolute upload path (inside /app/static/uploads/)
        upload_folder = os.path.join('app', 'static', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)

        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)

        # Relative path for use in templates (for static access)
        relative_path = os.path.join('uploads', filename)

        new_note = Notes(
            title=form.subject.data.strip(),
            branch=form.branch.data,
            semester=form.semester.data,
            filename=filename,
            filepath=relative_path,
            user_id=current_user.id
        )
        db.session.add(new_note)
        db.session.commit()

        flash("✅ Note uploaded successfully!", "success")
        return redirect(url_for('notes.view_notes'))

    return render_template('notes/upload_note.html', form=form)

# -----------------------------
# 🔹 Delete Notes Route
# -----------------------------
@notes_bp.route('/notes/delete/<int:note_id>', methods=['POST'], endpoint='delete_note')
@login_required
def delete_note(note_id):
    """
    Allows a user to delete their own uploaded note.
    """
    note = Notes.query.get_or_404(note_id)

    if note.user_id != current_user.id:
        flash("❌ You are not authorized to delete this note.", "danger")
        return redirect(url_for('notes.view_notes'))

    # Delete file from disk
    try:
        absolute_path = os.path.join('app', 'static', note.filepath)
        if os.path.exists(absolute_path):
            os.remove(absolute_path)
    except Exception as e:
        print("⚠️ File deletion failed:", e)

    db.session.delete(note)
    db.session.commit()

    flash("🗑️ Note deleted successfully!", "success")
    return redirect(url_for('notes.view_notes'))

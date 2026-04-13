from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_wtf.file import FileAllowed

# 🔹 Constants used for dropdowns
BRANCHES = ['CSE', 'ECE', 'ME', 'CE', 'EE', 'AU']
SEMESTERS = ['1', '2', '3', '4', '5', '6']

# -------------------------------
# 🔹 Form for uploading a note
# -------------------------------
class NoteUploadForm(FlaskForm):
    subject = StringField(
        "Subject",
        validators=[DataRequired(message="Subject is required.")]
    )
    branch = SelectField(
        "Branch",
        choices=[(branch, branch) for branch in BRANCHES],
        validators=[DataRequired(message="Please select a branch.")]
    )
    semester = SelectField(
        "Semester",
        choices=[(sem, sem) for sem in SEMESTERS],
        validators=[DataRequired(message="Please select a semester.")]
    )
    file = FileField(
        "Upload File",
        validators=[
            DataRequired(message="Please select a file."),
            FileAllowed(['pdf', 'docx', 'pptx', 'jpg', 'png'], "Allowed formats: pdf, docx, pptx, jpg, png")
        ]
    )
    submit = SubmitField("Upload Note")

# -----------------------------------
# 🔹 Form for filtering notes (Admin)
# -----------------------------------
class NoteFilterForm(FlaskForm):
    branch = SelectField(
        "Filter by Branch",
        choices=[('', 'All Branches')] + [(b, b) for b in BRANCHES]
    )
    semester = SelectField(
        "Filter by Semester",
        choices=[('', 'All Semesters')] + [(sem, sem) for sem in SEMESTERS]
    )
    submit = SubmitField("Filter Notes")

# -----------------------------------
# 🔹 Form for deleting a note
# -----------------------------------
class DeleteNoteForm(FlaskForm):
    submit = SubmitField("Delete")

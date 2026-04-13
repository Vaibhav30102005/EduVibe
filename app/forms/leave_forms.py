from flask_wtf import FlaskForm
from wtforms import StringField, FileField, SubmitField, SelectField, DateField
from wtforms.validators import DataRequired, Length, Optional
from flask_wtf.file import FileAllowed


# ------------------------------
# 🔹 Leave Application Form
# ------------------------------
class LeaveApplicationForm(FlaskForm):
    reason = StringField(
        "Reason for Leave",
        validators=[
            DataRequired(message="Please provide a reason."),
            Length(min=5, max=255, message="Reason must be between 5 and 255 characters.")
        ]
    )

    # ✅ New Fields Added
    from_date = DateField(
        "From Date",
        format="%Y-%m-%d",
        validators=[DataRequired(message="Please select the start date.")]
    )

    to_date = DateField(
        "To Date",
        format="%Y-%m-%d",
        validators=[DataRequired(message="Please select the end date.")]
    )

    document = FileField(
        "Upload Supporting Document (PDF only)",
        validators=[
            Optional(),
            FileAllowed(['pdf'], "Only PDF files are allowed.")
        ]
    )

    submit = SubmitField("Submit Leave Application")


# ------------------------------
# 🔹 Admin Approval Form (Updated)
# ------------------------------
class ApproveLeaveForm(FlaskForm):
    status = SelectField(
        'Update Status',
        choices=[
            ('Pending', 'Pending ⏳'),
            ('Approved', 'Approved ✅'),
            ('Rejected', 'Rejected ❌')
        ],
        validators=[DataRequired(message="Please select a status.")]
    )
    submit = SubmitField("Update Status")

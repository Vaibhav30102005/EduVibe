from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length

# ----------------------------
# 🔹 Form for CR Nomination
# ----------------------------
class CRNominationForm(FlaskForm):
    name = StringField(
        "Full Name",
        validators=[DataRequired(), Length(min=2, max=100)],
        render_kw={
            "placeholder": "Enter your full name",
            "class": "form-control"
        }
    )

    roll_no = StringField(
        "Roll Number",
        validators=[DataRequired(), Length(min=2, max=20)],
        render_kw={
            "placeholder": "Enter your roll number",
            "class": "form-control"
        }
    )

    branch = HiddenField()
    semester = HiddenField()

    manifesto = TextAreaField(
        "Manifesto (Why should others vote for you?)",
        validators=[Length(max=500)],
        render_kw={
            "placeholder": "Write a short reason (max 500 characters)",
            "class": "form-control",
            "rows": 4
        }
    )

    submit = SubmitField(
        "Nominate Myself",
        render_kw={"class": "btn btn-success mt-3"}
    )


# ----------------------------
# 🔹 Form for Voting
# ----------------------------
class CRVoteForm(FlaskForm):
    nominee_id = HiddenField("Nominee ID", validators=[DataRequired()])

    submit = SubmitField(
        "Vote",
        render_kw={"class": "btn btn-primary btn-sm"}
    )


# ----------------------------
# 🔹 Form for Admin Manage Voting
# ----------------------------
class ManageVotingForm(FlaskForm):
    branch = SelectField(
        "Branch",
        choices=[
            ("CSE", "CSE"),
            ("ECE", "ECE"),
            ("EEE", "EEE"),
            ("ME", "ME"),
            ("CE", "CE")
        ],
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )

    semester = SelectField(
        "Semester",
        choices=[
            ("1", "1"), ("2", "2"), ("3", "3"),
            ("4", "4"), ("5", "5"), ("6", "6")
        ],
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )

    submit = SubmitField(
        "Submit",
        render_kw={"class": "btn btn-primary mt-3"}
    )

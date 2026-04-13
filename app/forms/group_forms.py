from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SubmitField,
    PasswordField, SelectField
)
from wtforms.validators import DataRequired, Length

# ✅ List of available branches
BRANCHES = ['CSE', 'ECE', 'ME', 'CE', 'EE', 'AU']

# ✅ Form to create a study group
class GroupCreateForm(FlaskForm):
    name = StringField(
        'Group Name',
        validators=[DataRequired(), Length(min=2, max=100)],
        render_kw={"placeholder": "Enter group name", "class": "form-control"}
    )
    description = TextAreaField(
        'Description (Optional)',
        render_kw={
            "placeholder": "Enter group description (optional)",
            "rows": 3,
            "class": "form-control"
        }
    )
    group_password = PasswordField(
        'Group Password',
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Set group password",
            "class": "form-control"
        }
    )
    submit = SubmitField(
        'Create Group',
        render_kw={"class": "btn btn-success mt-3"}
    )

# ✅ Form to join a study group
class GroupJoinForm(FlaskForm):
    name = StringField(
        'Your Name',
        validators=[DataRequired(), Length(min=2, max=100)],
        render_kw={"placeholder": "Enter your name", "class": "form-control"}
    )
    roll_no = StringField(
        'Roll Number',
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter your roll number", "class": "form-control"}
    )
    branch = SelectField(
        'Branch',
        choices=[(b, b) for b in BRANCHES],
        validators=[DataRequired()],
        render_kw={"class": "form-select"}
    )
    code = StringField(
        'Group Code / ID',
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter group code", "class": "form-control"}
    )
    password = PasswordField(
        'Group Password',
        validators=[DataRequired()],
        render_kw={"placeholder": "Enter group password", "class": "form-control"}
    )
    submit = SubmitField(
        'Join Group',
        render_kw={"class": "btn btn-primary mt-3"}
    )

    # ✅ Compatibility alias for templates using `form.roll_number`
    @property
    def roll_number(self):
        return self.roll_no

# ✅ Form to send messages in group chat
class GroupMessageForm(FlaskForm):
    content = TextAreaField(
        'Message',
        validators=[DataRequired()],
        render_kw={
            "placeholder": "Type your message...",
            "rows": 2,
            "class": "form-control"
        }
    )
    submit = SubmitField(
        'Send',
        render_kw={"class": "btn btn-secondary mt-2"}
    )

# ✅ Form to edit group details
class EditGroupForm(FlaskForm):
    name = StringField(
        'Group Name',
        validators=[DataRequired()],
        render_kw={"placeholder": "Edit group name", "class": "form-control"}
    )
    description = TextAreaField(
        'Description',
        render_kw={"placeholder": "Edit group description", "rows": 3, "class": "form-control"}
    )
    # ✅ Added for compatibility with create_group.html template
    group_code = StringField(
        'Group Code / ID',
        render_kw={"readonly": True, "class": "form-control"}
    )
    group_password = PasswordField(
        'Group Password',
        render_kw={"readonly": True, "class": "form-control"}
    )
    submit = SubmitField(
        'Update Group',
        render_kw={"class": "btn btn-warning mt-2"}
    )

# ✅ Form to delete a group
class DeleteGroupForm(FlaskForm):
    submit = SubmitField(
        'Delete Group',
        render_kw={"class": "btn btn-danger"}
    )

# ✅ Form to leave a group
class LeaveGroupForm(FlaskForm):
    submit = SubmitField(
        'Leave Group',
        render_kw={"class": "btn btn-outline-danger mt-3"}
    )

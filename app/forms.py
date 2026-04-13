from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField,
    SelectField, TextAreaField, FileField, DateField, BooleanField
)
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError, Length
from flask_wtf.file import FileAllowed

# ─────────────────────────────
# Constants
# ─────────────────────────────
BRANCHES = ['CSE', 'ECE', 'ME', 'CE', 'EE', 'AU']
SEMESTERS = ['1', '2', '3', '4', '5', '6']
ROLES = [('student', 'Student'), ('cr', 'Class Representative'), ('admin', 'Admin')]

# ─────────────────────────────
# 🔹 Registration Form
# ─────────────────────────────
class RegistrationForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    roll_no = StringField('Roll Number', validators=[DataRequired(), Length(min=5, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role = SelectField('Role', choices=ROLES, validators=[DataRequired()])
    branch = SelectField('Branch', choices=[(b, b) for b in BRANCHES], validators=[DataRequired()])
    semester = SelectField('Semester', choices=[(s, s) for s in SEMESTERS], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_branch(self, field):
        if self.role.data != 'admin' and not field.data:
            raise ValidationError("Branch is required.")

    def validate_semester(self, field):
        if self.role.data != 'admin' and not field.data:
            raise ValidationError("Semester is required.")

# ─────────────────────────────
# 🔹 Login Form
# ─────────────────────────────
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

# ─────────────────────────────
# 🔹 Note Upload Form
# ─────────────────────────────
class NoteUploadForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    file = FileField('Upload File', validators=[
        DataRequired(),
        FileAllowed(['pdf', 'doc', 'docx', 'ppt', 'pptx'], 'Documents only!')
    ])
    branch = SelectField('Branch', choices=[(b, b) for b in BRANCHES], validators=[DataRequired()])
    semester = SelectField('Semester', choices=[(s, s) for s in SEMESTERS], validators=[DataRequired()])
    submit = SubmitField('Upload')

# ─────────────────────────────
# 🔹 Planner Task Form
# ─────────────────────────────
class PlannerTaskForm(FlaskForm):
    task_name = StringField('Task Name', validators=[DataRequired()])
    due_date = DateField('Due Date', format='%Y-%m-%d', validators=[DataRequired()])
    completed = BooleanField('Completed')
    submit = SubmitField('Add Task')

# ─────────────────────────────
# 🔹 Group Creation Form
# ─────────────────────────────
class GroupCreationForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Length(max=200)])
    group_code = StringField('Group Code', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Group Password', validators=[DataRequired(), Length(min=4, max=20)])
    submit = SubmitField('Create Group')

# ─────────────────────────────
# 🔹 Group Join Form
# ─────────────────────────────
class GroupJoinForm(FlaskForm):
    group_code = StringField('Group Code', validators=[DataRequired()])
    password = PasswordField('Group Password', validators=[DataRequired()])
    submit = SubmitField('Join Group')

# ─────────────────────────────
# 🔹 Group Chat Message Form
# ─────────────────────────────
class GroupMessageForm(FlaskForm):
    content = StringField('Message', validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField('Send')

# ─────────────────────────────
# 🔹 Group Edit Form
# ─────────────────────────────
class GroupEditForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Length(max=200)])
    group_code = StringField('Group Code', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Group Password', validators=[DataRequired(), Length(min=4, max=20)])
    submit = SubmitField('Update Group')



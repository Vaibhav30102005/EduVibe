# app/forms/auth_forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo

# 🔹 Sample branches and semesters (update as needed)
BRANCHES = ['CSE', 'ECE', 'ME', 'CE', 'EE', 'AU']
SEMESTERS = ['1', '2', '3', '4', '5', '6']

# 🔹 Registration Form
class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    
    # ✅ Added field: Roll Number
    roll_no = StringField('Roll Number', validators=[DataRequired()])
    
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField(
        'Confirm Password', validators=[DataRequired(), EqualTo('password')]
    )

    role = SelectField(
        'Role',
        choices=[
            ('student', 'Student'),
            ('cr', 'Class Representative'),
            ('admin', 'Admin')
        ],
        validators=[DataRequired()]
    )

    branch = SelectField(
        'Branch',
        choices=[(branch, branch) for branch in BRANCHES],
        validators=[DataRequired()]
    )

    semester = SelectField(
        'Semester',
        choices=[(sem, f'Semester {sem}') for sem in SEMESTERS],
        validators=[DataRequired()]
    )

    submit = SubmitField('Register')

# 🔹 Login Form
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

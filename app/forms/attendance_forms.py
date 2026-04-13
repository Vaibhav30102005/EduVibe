from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, SubmitField
from wtforms.validators import DataRequired

class AttendanceForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('Present', 'Present'), ('Absent', 'Absent')], validators=[DataRequired()])
    submit = SubmitField('Mark Attendance')

from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class FeedbackForm(FlaskForm):
    course_name = StringField('Course Name', validators=[DataRequired()])
    instructor_name = StringField('Instructor Name', validators=[DataRequired()])
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comments = TextAreaField('Comments (optional)')
    submit = SubmitField('Submit Feedback')

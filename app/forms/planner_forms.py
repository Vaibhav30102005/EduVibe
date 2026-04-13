# app/forms/planner_forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, SubmitField, BooleanField
from wtforms.validators import DataRequired

class PlannerTaskForm(FlaskForm):
    task_name = StringField(
        'Task Name',
        validators=[DataRequired()],
        render_kw={"class": "form-control", "placeholder": "Enter task name"}
    )

    description = TextAreaField(
        'Description',
        render_kw={"class": "form-control", "rows": 3, "placeholder": "Enter task description (optional)"}
    )

    due_date = DateField(
        'Due Date',
        validators=[DataRequired()],
        render_kw={"class": "form-control"}
    )

    completed = BooleanField(
        'Completed',
        render_kw={"class": "form-check-input"}
    )

    submit = SubmitField(
        'Add Task',
        render_kw={"class": "btn btn-success mt-3"}
    )

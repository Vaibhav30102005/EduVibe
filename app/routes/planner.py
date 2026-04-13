# app/routes/planner.py

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .. import db
from ..models import PlannerTask
from ..forms import PlannerTaskForm
from datetime import datetime

planner_bp = Blueprint('planner', __name__, url_prefix='/planner')

# 🔹 View + Add Tasks
@planner_bp.route('/', methods=['GET', 'POST'])
@login_required
def view_planner():
    form = PlannerTaskForm()

    if form.validate_on_submit():
        new_task = PlannerTask(
            task_name=form.task_name.data,
            due_date=form.due_date.data,
            completed=form.completed.data,
            owner=current_user
        )
        db.session.add(new_task)
        db.session.commit()
        flash('✅ Task added successfully!', 'success')
        return redirect(url_for('planner.view_planner'))

    tasks = PlannerTask.query.filter_by(user_id=current_user.id).order_by(PlannerTask.due_date).all()
    return render_template('planner.html', form=form, tasks=tasks)


# 🔹 Mark Task as Completed
@planner_bp.route('/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = PlannerTask.query.get_or_404(task_id)

    if task.owner != current_user:
        flash("⛔ You are not authorized to modify this task.", 'danger')
        return redirect(url_for('planner.view_planner'))

    task.completed = True
    db.session.commit()
    flash('✅ Task marked as completed!', 'info')
    return redirect(url_for('planner.view_planner'))


# 🔹 Delete Task
@planner_bp.route('/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = PlannerTask.query.get_or_404(task_id)

    if task.owner != current_user:
        flash("⛔ You are not authorized to delete this task.", 'danger')
        return redirect(url_for('planner.view_planner'))

    db.session.delete(task)
    db.session.commit()
    flash('🗑️ Task deleted from your planner.', 'info')
    return redirect(url_for('planner.view_planner'))


# 🔹 Edit Task (NEWLY ADDED)
@planner_bp.route('/edit/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = PlannerTask.query.get_or_404(task_id)

    if task.owner != current_user:
        flash("⛔ You are not authorized to edit this task.", 'danger')
        return redirect(url_for('planner.view_planner'))

    form = PlannerTaskForm(obj=task)  # pre-fill with current task data

    if request.method == 'POST' and form.validate_on_submit():
        task.task_name = form.task_name.data
        task.due_date = form.due_date.data
        task.completed = form.completed.data
        db.session.commit()
        flash('✏️ Task updated successfully!', 'success')
        return redirect(url_for('planner.view_planner'))

    return render_template('edit_task.html', form=form, task=task)

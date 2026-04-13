from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import Routine
from app import db

routine_bp = Blueprint('routine', __name__, url_prefix='/routine')


from datetime import datetime

@routine_bp.route('/')
@login_required
def view_routine():
    show_today = request.args.get('today') == '1'
    today_name = datetime.today().strftime('%A')  # e.g., 'Monday'

    # Fetch all entries for this user's branch & semester
    all_entries = Routine.query.filter_by(
        branch=current_user.branch,
        semester=current_user.semester
    ).order_by(Routine.day, Routine.time).all()

    from collections import defaultdict, OrderedDict
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    grouped = defaultdict(list)

    for entry in all_entries:
        day = entry.day.capitalize()
        if show_today and day != today_name:
            continue  # skip if not today's day
        grouped[day].append(entry)

    routine_by_day = OrderedDict()
    for day in day_order:
        if day in grouped:
            routine_by_day[day] = grouped[day]

    return render_template('routine/view_routine.html',
                           routine_by_day=routine_by_day,
                           show_today=show_today,
                           today=today_name)




@routine_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_routine():
    if current_user.role != 'cr':
        flash("Access denied", "danger")
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        routine = Routine(
            branch=current_user.branch,
            semester=current_user.semester,
            day=request.form['day'],
            subject=request.form['subject'],
            time=request.form['time'],
            room=request.form['room'],
            faculty=request.form['faculty']
        )
        db.session.add(routine)
        db.session.commit()
        flash("Routine added successfully", "success")
        return redirect(url_for('routine.view_routine'))

    return render_template('routine/add_routine.html')


@routine_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_routine(id):
    routine = Routine.query.get_or_404(id)
    if current_user.role != 'cr' or routine.branch != current_user.branch or routine.semester != current_user.semester:
        flash("Access denied", "danger")
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        routine.day = request.form['day']
        routine.subject = request.form['subject']
        routine.time = request.form['time']
        routine.room = request.form['room']
        routine.faculty = request.form['faculty']
        db.session.commit()
        flash("Routine updated", "success")
        return redirect(url_for('routine.view_routine'))

    return render_template('routine/edit_routine.html', routine=routine)


@routine_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_routine(id):
    routine = Routine.query.get_or_404(id)
    if current_user.role != 'cr' or routine.branch != current_user.branch or routine.semester != current_user.semester:
        flash("Access denied", "danger")
        return redirect(url_for('dashboard.index'))

    db.session.delete(routine)
    db.session.commit()
    flash("Routine deleted", "info")
    return redirect(url_for('routine.view_routine'))

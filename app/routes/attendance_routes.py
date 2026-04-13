from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file
from flask_login import login_required, current_user
from datetime import date, datetime
from io import BytesIO
from fpdf import FPDF

from app import db
from app.models import User, Attendance
from app.forms.attendance_forms import AttendanceForm

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


def is_admin_or_cr():
    return current_user.role in ['admin', 'cr']


# ----------------------------
# 📌 Student / CR / Admin View
# ----------------------------
@attendance_bp.route('/')
@login_required
def index():
    if current_user.role == 'student':
        student_id = current_user.id

    elif current_user.role in ['cr', 'admin']:
        student_id = request.args.get('student_id', type=int)
        if not student_id:
            flash("Please select a student to view attendance.", "warning")
            return redirect(url_for('dashboard.index'))

        student = User.query.get(student_id)
        if not student or student.role != 'student':
            flash("Invalid student.", "danger")
            return redirect(url_for('dashboard.index'))

        # Restrict CRs and Admins to same-branch students
        if student.branch != current_user.branch:
            flash("Access denied. You can only view attendance for your own branch.", "danger")
            return redirect(url_for('dashboard.index'))

        # CR also checks semester
        if current_user.role == 'cr' and student.semester != current_user.semester:
            flash("Access denied. You can only view your semester students.", "danger")
            return redirect(url_for('dashboard.index'))

    else:
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.index'))

    records = Attendance.query.filter_by(student_id=student_id).order_by(Attendance.date.desc()).all()
    total_days = len(records)
    present_days = sum(1 for record in records if record.status == 'Present')
    attendance_percentage = (present_days / total_days) * 100 if total_days > 0 else 0

    return render_template(
        'attendance/student_view.html',
        records=records,
        percentage=attendance_percentage,
        show_popup=(attendance_percentage < 75 and current_user.id == student_id)
    )


# ----------------------------
# 📌 Mark Attendance (Admin only, Today only)
# ----------------------------
@attendance_bp.route('/mark', methods=['GET', 'POST'])
@login_required
def mark_attendance():
    if current_user.role != 'admin':
        flash("Only Admin can mark attendance!", "danger")
        return redirect(url_for('attendance.index'))

    selected_branch = current_user.branch
    selected_semester = request.args.get('semester')

    semesters = [row[0] for row in db.session.query(User.semester)
                 .filter(User.branch == selected_branch, User.semester != None)
                 .distinct()]
    branches = [selected_branch]  # Only one

    students_query = User.query.filter_by(role='student', branch=selected_branch)
    if selected_semester:
        students_query = students_query.filter_by(semester=selected_semester)

    students = students_query.order_by(User.name).all()

    if request.method == 'POST':
        selected_date_str = request.form.get('date')
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash("Invalid date format.", "danger")
            return redirect(request.url)

        # ✅ Validation: Only today's attendance can be marked
        if selected_date != date.today():
            flash("Admins can only mark attendance for today's date!", "danger")
            return redirect(request.url)

        for student in students:
            status = request.form.get(f'status_{student.id}')
            if status:
                existing = Attendance.query.filter_by(student_id=student.id, date=selected_date).first()
                if existing:
                    existing.status = status
                else:
                    new_record = Attendance(
                        student_id=student.id,
                        date=selected_date,
                        status=status,
                        marked_by_id=current_user.id
                    )
                    db.session.add(new_record)

        db.session.commit()
        flash("Attendance marked successfully!", "success")
        return redirect(url_for('attendance.attendance_summary'))

    return render_template(
        'attendance/mark_attendance.html',
        students=students,
        today=date.today(),
        is_admin=True,
        selected_branch=selected_branch,
        selected_semester=selected_semester,
        branches=branches,
        semesters=semesters
    )


# ----------------------------
# 📌 Edit Attendance (Admin only)
# ----------------------------
@attendance_bp.route('/edit/<int:record_id>', methods=['GET', 'POST'])
@login_required
def edit(record_id):
    if current_user.role != 'admin':
        flash("Only Admin can edit attendance!", "danger")
        return redirect(url_for('attendance.index'))

    record = Attendance.query.get_or_404(record_id)
    student = User.query.get_or_404(record.student_id)

    if student.branch != current_user.branch:
        flash("Access denied. You can only edit records from your branch.", "danger")
        return redirect(url_for('attendance.index'))

    form = AttendanceForm(obj=record)
    if form.validate_on_submit():
        record.status = form.status.data
        record.date = form.date.data
        db.session.commit()
        flash("Attendance updated.", "success")
        return redirect(url_for('attendance.index'))

    return render_template('attendance/edit.html', form=form, record=record)


# ----------------------------
# 📌 Delete Attendance (Admin only)
# ----------------------------
@attendance_bp.route('/delete/<int:record_id>', methods=['POST'])
@login_required
def delete(record_id):
    if current_user.role != 'admin':
        flash("Only Admin can delete attendance!", "danger")
        return redirect(url_for('attendance.index'))

    record = Attendance.query.get_or_404(record_id)
    student = User.query.get_or_404(record.student_id)

    if student.branch != current_user.branch:
        flash("Access denied. You can only delete records from your branch.", "danger")
        return redirect(url_for('attendance.index'))

    db.session.delete(record)
    db.session.commit()
    flash("Attendance deleted successfully.", "info")
    return redirect(url_for('attendance.index'))


# ----------------------------
# 📌 Attendance Summary
# ----------------------------
@attendance_bp.route('/summary')
@login_required
def attendance_summary():
    role = current_user.role
    students = []

    if role == 'admin':
        selected_branch = current_user.branch
        selected_semester = request.args.get('semester')

        query = User.query.filter_by(role='student', branch=selected_branch)
        if selected_semester:
            query = query.filter_by(semester=selected_semester)

        students = query.all()

    elif role == 'cr':
        students = User.query.filter_by(
            role='student',
            branch=current_user.branch,
            semester=current_user.semester
        ).all()

    elif role == 'student':
        students = [current_user]

    else:
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.index'))

    student_summaries = []
    for student in students:
        total_days = Attendance.query.filter_by(student_id=student.id).count()
        present_days = Attendance.query.filter_by(student_id=student.id, status='Present').count()
        percentage = (present_days / total_days) * 100 if total_days > 0 else 0

        student_summaries.append({
            'name': student.name,
            'roll_no': student.roll_no,
            'branch': student.branch,
            'semester': student.semester,
            'present': present_days,
            'total': total_days,
            'percentage': round(percentage, 2)
        })

    branches = [current_user.branch] if role == 'admin' else []
    semesters = [s[0] for s in db.session.query(User.semester).filter_by(branch=current_user.branch).distinct()] if role == 'admin' else []

    return render_template(
        'attendance/summary.html',
        students=student_summaries,
        branches=branches,
        semesters=semesters,
        selected_branch=current_user.branch if role == 'admin' else '',
        selected_semester=request.args.get('semester', '')
    )


# ----------------------------
# 📌 Attendance PDF Download (CR & Admin only)
# ----------------------------
@attendance_bp.route('/download_pdf')
@login_required
def download_pdf():
    if current_user.role == 'cr':
        students = User.query.filter_by(
            branch=current_user.branch,
            semester=current_user.semester,
            role='student'
        ).all()
    elif current_user.role == 'admin':
        students = User.query.filter_by(
            branch=current_user.branch,
            role='student'
        ).all()
    else:
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.index'))

    # Generate PDF with table format
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(200, 10, txt=f"Attendance Summary - {current_user.branch}", ln=True, align="C")
    pdf.ln(10)

    # Table Header
    pdf.set_font("Arial", "B", 10)
    pdf.cell(40, 10, "Name", 1)
    pdf.cell(25, 10, "Roll No", 1)
    pdf.cell(25, 10, "Branch", 1)
    pdf.cell(25, 10, "Semester", 1)
    pdf.cell(25, 10, "Present", 1)
    pdf.cell(25, 10, "Total", 1)
    pdf.cell(25, 10, "Percent", 1, ln=True)

    # Table Rows
    pdf.set_font("Arial", size=9)
    for student in students:
        total_days = Attendance.query.filter_by(student_id=student.id).count()
        present_days = Attendance.query.filter_by(student_id=student.id, status='Present').count()
        percent = round((present_days / total_days) * 100, 2) if total_days > 0 else 0

        pdf.cell(40, 10, student.name, 1)
        pdf.cell(25, 10, str(student.roll_no), 1)
        pdf.cell(25, 10, student.branch, 1)
        pdf.cell(25, 10, str(student.semester), 1)
        pdf.cell(25, 10, str(present_days), 1)
        pdf.cell(25, 10, str(total_days), 1)
        pdf.cell(25, 10, f"{percent}%", 1, ln=True)

    # ✅ Output full PDF
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    pdf_output = BytesIO(pdf_bytes)

    return send_file(pdf_output, as_attachment=True,
                     download_name="attendance_report.pdf",
                     mimetype="application/pdf")

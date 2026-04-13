# app/routes/cr_voting.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, make_response
from flask_login import login_required, current_user
from app.forms.cr_forms import CRNominationForm, CRVoteForm, ManageVotingForm
from app.models import db, User, CRCandidate, CRVote, CRVotingSession
import csv
from io import StringIO
from fpdf import FPDF
import tempfile
import os

cr_bp = Blueprint('cr_bp', __name__, url_prefix='/cr')

# ----------------------------
# 🔹 Admin Manage Voting Page
# ----------------------------
@cr_bp.route('/manage', methods=['GET', 'POST'])
@login_required
def manage_voting():
    """Admin page to manage voting sessions (Start/Stop). 
       Admin can only manage sessions for their own branch."""
    if current_user.role != 'admin':
        flash("Only Admin can manage voting.", "danger")
        return redirect(url_for('dashboard.index'))

    # Enforce admin branch scope
    admin_branch = current_user.branch
    if not admin_branch:
        flash("Your admin profile has no branch assigned. Contact support.", "danger")
        return redirect(url_for('dashboard.index'))

    form = ManageVotingForm()

    # Optional GET filter for semester; branch is forced to admin branch
    branch = request.args.get('branch', admin_branch)
    if branch != admin_branch:
        flash("You can manage voting only for your own branch.", "warning")
        return redirect(url_for('cr_bp.manage_voting', branch=admin_branch))

    semester = request.args.get('semester')

    # Latest session for this branch & (optional) semester
    if semester:
        voting_session = (CRVotingSession.query
                          .filter_by(branch=admin_branch, semester=semester)
                          .order_by(CRVotingSession.id.desc())
                          .first())
    else:
        voting_session = (CRVotingSession.query
                          .filter_by(branch=admin_branch)
                          .order_by(CRVotingSession.id.desc())
                          .first())

    # List of sessions (for this admin branch)
    sessions = (CRVotingSession.query
                .filter_by(branch=admin_branch)
                .order_by(CRVotingSession.id.desc())
                .all())

    return render_template("cr/manage_voting.html", form=form,
                           voting_session=voting_session, sessions=sessions)


# ----------------------------
# 🔹 Start Voting (Admin Only)
# ----------------------------
@cr_bp.route('/session/start', methods=['POST'])
@login_required
def start_voting():
    """Start a new voting session for a branch/semester.
       Admin can only start for their own branch.
       Multiple starts allowed (creates new session each time)."""
    if current_user.role != 'admin':
        flash("Only Admin can start voting.", "danger")
        return redirect(url_for('dashboard.index'))

    admin_branch = current_user.branch
    if not admin_branch:
        flash("Your admin profile has no branch assigned. Contact support.", "danger")
        return redirect(url_for('dashboard.index'))

    branch = request.form.get('branch')
    semester = request.form.get('semester')

    # Restrict admin to own branch only
    if branch != admin_branch:
        flash("You can only start voting for your own branch.", "warning")
        return redirect(url_for('cr_bp.manage_voting', branch=admin_branch, semester=semester or ""))

    if not branch or not semester:
        flash("Please select both Branch and Semester.", "warning")
        return redirect(url_for('cr_bp.manage_voting', branch=admin_branch, semester=semester or ""))

    # ----------------------------
    # 🔹 Purane nominations & votes delete karo (RESET only for this branch+semester)
    # ----------------------------
    old_candidates = CRCandidate.query.filter_by(branch=branch, semester=semester).all()
    for candidate in old_candidates:
        CRVote.query.filter_by(candidate_id=candidate.id).delete()
        db.session.delete(candidate)
    db.session.commit()

    # Always create a new session, allowing multiple cycles
    session = CRVotingSession(branch=branch, semester=semester, is_active=True, has_ended=False)
    db.session.add(session)
    db.session.commit()

    flash(f"✅ New voting session started for {branch} Sem {semester}!", "success")
    return redirect(url_for('cr_bp.manage_voting', branch=branch, semester=semester))


# ----------------------------
# 🔹 End Voting (Admin Only)
# ----------------------------
@cr_bp.route('/session/end', methods=['POST'])
@login_required
def end_voting():
    """End the latest active voting session for branch/semester.
       Admin can only end for their own branch."""
    if current_user.role != 'admin':
        flash("Only Admin can end voting.", "danger")
        return redirect(url_for('dashboard.index'))

    admin_branch = current_user.branch
    if not admin_branch:
        flash("Your admin profile has no branch assigned. Contact support.", "danger")
        return redirect(url_for('dashboard.index'))

    branch = request.form.get('branch')
    semester = request.form.get('semester')

    if branch != admin_branch:
        flash("You can only stop voting for your own branch.", "warning")
        return redirect(url_for('cr_bp.manage_voting', branch=admin_branch, semester=semester or ""))

    if not branch or not semester:
        flash("Please select both Branch and Semester.", "warning")
        return redirect(url_for('cr_bp.manage_voting', branch=admin_branch, semester=semester or ""))

    # Get latest active session for this branch/semester
    session = (CRVotingSession.query
               .filter_by(branch=branch, semester=semester, is_active=True)
               .order_by(CRVotingSession.id.desc())
               .first())
    if not session:
        flash("⚠️ No active session found for this branch/semester.", "warning")
        return redirect(url_for('cr_bp.manage_voting', branch=branch, semester=semester))

    # End the active session
    session.is_active = False
    session.has_ended = True
    db.session.commit()

    flash(f"🛑 Voting ended for {branch} Sem {semester}!", "success")
    return redirect(url_for('cr_bp.results', branch=branch, semester=semester))


# ----------------------------
# 🔹 Nomination (Students Only)
# ----------------------------
@cr_bp.route('/nominate', methods=['GET', 'POST'])
@login_required
def nominate():
    if current_user.role != 'student':
        flash("Only students can nominate for CR position.", "danger")
        return redirect(url_for('dashboard.index'))

    existing = CRCandidate.query.filter_by(user_id=current_user.id).first()
    if existing:
        flash("You have already nominated yourself.", "info")
        return redirect(url_for('cr_bp.nominations'))

    form = CRNominationForm()
    form.name.data = current_user.name
    form.roll_no.data = current_user.roll_no
    form.branch.data = current_user.branch
    form.semester.data = current_user.semester

    if form.validate_on_submit():
        candidate = CRCandidate(
            user_id=current_user.id,
            branch=current_user.branch,
            semester=current_user.semester,
            manifesto=form.manifesto.data
        )
        db.session.add(candidate)
        db.session.commit()
        flash("Nomination submitted successfully!", "success")
        return redirect(url_for('cr_bp.nominations'))

    return render_template('cr/nominate.html', form=form)


# ----------------------------
# 🔹 View Nominees & Vote
# ----------------------------
@cr_bp.route('/nominations', methods=['GET', 'POST'])
@login_required
def nominations():
    if current_user.role not in ['student', 'cr']:
        flash("Only students and CRs can vote.", "danger")
        return redirect(url_for('dashboard.index'))

    # Check latest active session for user's branch & semester
    session = (CRVotingSession.query
               .filter_by(branch=current_user.branch, semester=current_user.semester, is_active=True)
               .order_by(CRVotingSession.id.desc())
               .first())
    if not session:
        flash("Voting has not started yet. Please wait for Admin.", "info")
        return redirect(url_for('dashboard.index'))

    candidates = CRCandidate.query.filter_by(
        branch=current_user.branch,
        semester=current_user.semester
    ).all()

    has_voted = CRVote.query.filter_by(voter_id=current_user.id).first()
    already_nominated = CRCandidate.query.filter_by(user_id=current_user.id).first()

    if request.method == 'POST':
        nominee_user_id = request.form.get('nominee_id')
        if not nominee_user_id:
            flash("Invalid vote submission.", "danger")
            return redirect(url_for('cr_bp.nominations'))

        # Find candidate row by user_id
        candidate = CRCandidate.query.filter_by(user_id=int(nominee_user_id)).first()
        if not candidate:
            flash("Invalid candidate selected.", "danger")
            return redirect(url_for('cr_bp.nominations'))

        if already_nominated:
            flash("Nominees are not allowed to vote.", "danger")
        elif has_voted:
            flash("You have already voted.", "info")
        else:
            vote = CRVote(voter_id=current_user.id, candidate_id=candidate.id)
            db.session.add(vote)
            db.session.commit()
            flash("✅ Your vote has been recorded.", "success")

        return redirect(url_for('cr_bp.nominations'))

    vote_form = CRVoteForm()
    nominees = [c.nominee for c in candidates if c.nominee]

    return render_template(
        'cr/vote.html',
        nominees=nominees,
        vote_form=vote_form,
        has_voted=has_voted,
        already_nominated=already_nominated
    )


# ----------------------------
# 🔹 Show Results
# ----------------------------
@cr_bp.route('/results')
@login_required
def results():
    if current_user.role not in ['student', 'cr', 'admin']:
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard.index'))

    # Filters; default to current user's branch/sem
    branch_filter = request.args.get('branch', current_user.branch)
    sem_filter = request.args.get('semester', current_user.semester)

    # Only latest ended session matters for results page
    session = (CRVotingSession.query
               .filter_by(branch=branch_filter, semester=sem_filter)
               .order_by(CRVotingSession.id.desc())
               .first())
    if not session or not session.has_ended:
        flash("⚠️ Please wait for vote ending.", "warning")
        return render_template('cr/results_pending.html')

    candidates = CRCandidate.query.filter_by(branch=branch_filter, semester=sem_filter).all()
    results = []

    for c in candidates:
        if c.nominee:
            vote_count = CRVote.query.filter_by(candidate_id=c.id).count()
            results.append({
                "name": c.nominee.name,
                "roll_no": c.nominee.roll_no,
                "branch": c.branch,
                "semester": c.semester,
                "votes": vote_count
            })

    # Sort by votes desc
    results.sort(key=lambda r: r["votes"], reverse=True)

    # Chart data for template
    chart_data = [{"name": r["name"], "votes": r["votes"]} for r in results]

    return render_template(
        'cr/results.html',
        results=results,
        chart_data=chart_data,
        selected_branch=branch_filter,
        selected_semester=sem_filter
    )


# ----------------------------
# 🔹 Export Results as CSV
# ----------------------------
@cr_bp.route('/results/export/csv')
@login_required
def export_results_csv():
    """Exports results as CSV. Accepts optional ?branch=&semester= filters."""
    branch_filter = request.args.get('branch', current_user.branch)
    sem_filter = request.args.get('semester', current_user.semester)

    candidates = CRCandidate.query
    if branch_filter:
        candidates = candidates.filter_by(branch=branch_filter)
    if sem_filter:
        candidates = candidates.filter_by(semester=sem_filter)
    candidates = candidates.all()

    results = []
    for c in candidates:
        if c.nominee:
            results.append({
                "name": c.nominee.name,
                "roll_no": c.nominee.roll_no,
                "branch": c.branch,
                "semester": c.semester,
                "votes": CRVote.query.filter_by(candidate_id=c.id).count()
            })

    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["name", "roll_no", "branch", "semester", "votes"])
    writer.writeheader()
    writer.writerows(results)

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=cr_results.csv"
    response.headers["Content-type"] = "text/csv"
    return response


# ----------------------------
# 🔹 Export Results as PDF
# ----------------------------
@cr_bp.route('/results/export/pdf')
@login_required
def export_results_pdf():
    """Exports results as PDF. Accepts optional ?branch=&semester= filters."""
    branch_filter = request.args.get('branch', current_user.branch)
    sem_filter = request.args.get('semester', current_user.semester)

    candidates = CRCandidate.query
    if branch_filter:
        candidates = candidates.filter_by(branch=branch_filter)
    if sem_filter:
        candidates = candidates.filter_by(semester=sem_filter)
    candidates = candidates.all()

    results = []
    for c in candidates:
        if c.nominee:
            results.append({
                "name": c.nominee.name,
                "roll_no": c.nominee.roll_no,
                "branch": c.branch,
                "semester": c.semester,
                "votes": CRVote.query.filter_by(candidate_id=c.id).count()
            })

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        filepath = tmp_file.name
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="CR Voting Results", ln=True, align='C')
        pdf.ln(10)

        for r in results:
            line = f"{r['name']} ({r['roll_no']}) - {r['branch']} Sem {r['semester']} => {r['votes']} Votes"
            pdf.cell(200, 10, txt=line, ln=True)

        pdf.output(filepath)

    with open(filepath, "rb") as f:
        pdf_data = f.read()
    os.remove(filepath)

    response = make_response(pdf_data)
    response.headers["Content-Disposition"] = "attachment; filename=cr_results.pdf"
    response.headers["Content-type"] = "application/pdf"
    return response

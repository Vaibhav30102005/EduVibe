from flask import Blueprint, render_template
from flask_login import login_required, current_user

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # Check the user's role and load the appropriate dashboard
    if current_user.role == 'student':
        return render_template('dashboard.html', role='Student', user=current_user)

    elif current_user.role == 'cr':
        return render_template('dashboard.html', role='Class Representative', user=current_user)

    elif current_user.role == 'admin':
        return render_template('dashboard.html', role='Admin', user=current_user)

    else:
        return render_template('dashboard.html', role='Unknown', user=current_user)

from . import db, login_manager
from flask_login import UserMixin
from datetime import datetime
import pytz   

# ✅ Define IST timezone
IST = pytz.timezone("Asia/Kolkata")

def ist_now():
    """Return current time in IST timezone"""
    return datetime.now(IST)

# ------------------------
# 🔹 User Loader
# ------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ------------------------
# 🔹 User Model
# ------------------------
class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    roll_no = db.Column(db.String(20), unique=True, nullable=True)  # ✅ nullable allowed
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), default='student', nullable=False)
    branch = db.Column(db.String(10), nullable=True)
    semester = db.Column(db.String(10), nullable=True)

    # Relationships
    notes = db.relationship('Notes', backref='author', lazy=True, cascade="all, delete-orphan")
    tasks = db.relationship('PlannerTask', backref='owner', lazy=True, cascade="all, delete-orphan")
    created_groups = db.relationship('Group', backref='creator', lazy=True, cascade="all, delete-orphan")
    group_memberships = db.relationship('GroupMembership', backref='user', lazy=True, cascade="all, delete-orphan")
    group_messages = db.relationship('GroupMessage', backref='user', lazy=True, cascade="all, delete-orphan")

    attendances_marked = db.relationship('Attendance', foreign_keys='Attendance.marked_by_id', backref='marked_by', lazy=True)
    attendances = db.relationship('Attendance', foreign_keys='Attendance.student_id', backref='student', lazy=True)

    complaints = db.relationship('Complaint', foreign_keys='Complaint.student_id', backref='student', lazy=True)
    complaints_resolved = db.relationship('Complaint', foreign_keys='Complaint.resolved_by_id', backref='resolver', lazy=True)

    feedbacks = db.relationship('Feedback', backref='student', lazy=True)

    doubts_asked = db.relationship('Doubt', foreign_keys='Doubt.student_id', backref='student', lazy=True)
    doubts_resolved = db.relationship('Doubt', foreign_keys='Doubt.resolved_by_id', backref='resolver', lazy=True)

    cr_nominations = db.relationship('CRCandidate', backref='nominee', lazy=True, cascade="all, delete-orphan")
    cr_votes = db.relationship('CRVote', backref='voter', lazy=True, cascade="all, delete-orphan")

    leave_applications = db.relationship('LeaveApplication', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.name} ({self.role}) | {self.email}>"

    def is_student_or_cr(self):
        return self.role in ['student', 'cr']


# ------------------------
# 🔹 Notes Model
# ------------------------
class Notes(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=ist_now)

    branch = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.String(10), nullable=False)

    filename = db.Column(db.String(255), nullable=True)
    filepath = db.Column(db.String(500), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Note {self.title} | Branch: {self.branch}, Sem: {self.semester}>"


# ------------------------
# 🔹 Planner Task Model
# ------------------------
class PlannerTask(db.Model):
    __tablename__ = 'planner_task'

    id = db.Column(db.Integer, primary_key=True)
    task_name = db.Column(db.String(150), nullable=False)
    due_date = db.Column(db.DateTime, nullable=False)
    completed = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Task {self.task_name} | Due: {self.due_date}>"


# ------------------------
# 🔹 Study Group Model
# ------------------------
class Group(db.Model):
    __tablename__ = 'study_group'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    group_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    group_password = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=ist_now)

    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    branch = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.String(10), nullable=False)

    members = db.relationship('GroupMembership', backref='group', lazy='select', cascade="all, delete-orphan")
    messages = db.relationship('GroupMessage', backref='group', lazy='select', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Group {self.name} | Code: {self.group_code}>"

    def is_user_eligible(self, user):
        return (
            user.is_student_or_cr() and
            self.branch == user.branch and
            self.semester == user.semester
        )

    def has_user_joined(self, user):
        return GroupMembership.query.filter_by(user_id=user.id, group_id=self.id).first() is not None

    def is_group_full(self):
        return len(self.members) >= 5


# ------------------------
# 🔹 Group Membership
# ------------------------
class GroupMembership(db.Model):
    __tablename__ = 'group_membership'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'group_id', name='unique_user_group_membership'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=False)

    name = db.Column(db.String(150), nullable=False)
    roll_number = db.Column(db.String(20), nullable=False)
    branch = db.Column(db.String(50), nullable=False)
    joined_at = db.Column(db.DateTime, default=ist_now)

    def __repr__(self):
        return f"<Membership {self.name} | Group ID: {self.group_id}>"


# ------------------------
# 🔹 Group Message
# ------------------------
class GroupMessage(db.Model):
    __tablename__ = 'group_message'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=ist_now)

    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Message by User {self.user_id} | Group {self.group_id}>"


# ------------------------
# 🔹 Attendance
# ------------------------
class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False)
    marked_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"<Attendance {self.student.name} - {self.date} - {self.status}>"


# ------------------------
# 🔹 Feedback
# ------------------------
class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    instructor_name = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)

    def __repr__(self):
        return f"<Feedback | {self.course_name} | {self.rating}>"


# ------------------------
# 🔹 Doubt
# ------------------------
class Doubt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=ist_now)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return f"<Doubt {self.id} | Asked by {self.student_id}>"


# ------------------------
# 🔹 Complaint
# ------------------------
class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    response = db.Column(db.Text)
    resolved_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=ist_now)

    # ✅ New field to handle CR/Admin vs Admin-only complaints
    visibility = db.Column(db.String(20), default="cr_admin")  
    # allowed values: "cr_admin" or "admin"

    def __repr__(self):
        return f"<Complaint {self.title} | Status: {self.status}>"


# ------------------------
# 🔹 Routine
# ------------------------
class Routine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    day = db.Column(db.String(15), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    room = db.Column(db.String(50))
    faculty = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=ist_now)

    def __repr__(self):
        return f"<Routine {self.day} | {self.subject}>"


# ------------------------
# 🗳️ CR Voting Models
# ------------------------
class CRCandidate(db.Model):
    __tablename__ = 'cr_candidate'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    branch = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    manifesto = db.Column(db.Text, nullable=True)
    nominated_at = db.Column(db.DateTime, default=ist_now)

    votes = db.relationship(
        'CRVote',
        backref='candidate',
        lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CRCandidate {self.nominee.name} | {self.branch} - Sem {self.semester}>"


class CRVote(db.Model):
    __tablename__ = 'cr_vote'

    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey('cr_candidate.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=ist_now)

    def __repr__(self):
        return f"<CRVote by {self.voter_id} for {self.candidate_id}>"


# ✅ Admin control for CR Voting
class CRVotingControl(db.Model):
    __tablename__ = 'cr_voting_control'

    id = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.String(10), nullable=False)
    is_active = db.Column(db.Boolean, default=False)   # ✅ Admin ne approve kiya ya nahi
    is_finished = db.Column(db.Boolean, default=False) # ✅ Voting complete ya nahi
    created_at = db.Column(db.DateTime, default=ist_now)

    def __repr__(self):
        return f"<CRVotingControl {self.branch} Sem {self.semester} | Active: {self.is_active} | Finished: {self.is_finished}>"


# ✅ Voting Session tracking
class CRVotingSession(db.Model):
    __tablename__ = 'cr_voting_session'

    id = db.Column(db.Integer, primary_key=True)
    branch = db.Column(db.String(10), nullable=False)
    semester = db.Column(db.String(10), nullable=False)

    is_active = db.Column(db.Boolean, default=False)  # ✅ Voting started or not
    has_ended = db.Column(db.Boolean, default=False)  # ✅ Voting ended or not

    started_at = db.Column(db.DateTime, default=None)
    ended_at = db.Column(db.DateTime, default=None)

    def __repr__(self):
        return f"<CRVotingSession Branch={self.branch}, Sem={self.semester}, Active={self.is_active}, Ended={self.has_ended}>"


# ------------------------
# 🔹 Portfolio
# ------------------------
class Portfolio(db.Model):
    __tablename__ = 'portfolio'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    cr_id = db.Column(db.Integer, db.ForeignKey('user.id'))  
    profile_pic = db.Column(db.String(255))
    resume = db.Column(db.String(255))
    certificates = db.Column(db.String(255))
    achievements = db.Column(db.Text)
    skills = db.Column(db.Text)
    interests = db.Column(db.Text)
    github_link = db.Column(db.String(255))
    linkedin_link = db.Column(db.String(255))
    uploaded_at = db.Column(db.DateTime)

    student = db.relationship('User', foreign_keys=[student_id], backref='student_portfolios')
    cr = db.relationship('User', foreign_keys=[cr_id], backref='cr_portfolios')


# ------------------------
# 🔹 Leave Application
# ------------------------
class LeaveApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reason = db.Column(db.String(255), nullable=False)

    # ✅ New fields for leave duration
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)

    file_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=ist_now)
    status = db.Column(db.String(20), default='Pending')

    def __repr__(self):
        return f"<LeaveApplication {self.id} | {self.from_date} → {self.to_date} | Status: {self.status}>"

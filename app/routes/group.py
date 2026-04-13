
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from app import db
from app.models import Group, GroupMembership, User, GroupMessage
from app.forms.group_forms import GroupCreateForm, GroupJoinForm, GroupMessageForm

group_bp = Blueprint('group', __name__, url_prefix='/groups')

@group_bp.route('/')
@login_required
def list_groups():
    groups = Group.query.order_by(Group.created_at.desc()).all()
    joined_group_ids = {m.group_id for m in current_user.group_memberships}
    return render_template('group/group_list.html', groups=groups, joined_group_ids=joined_group_ids)

@group_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if current_user.role != 'student':
        flash('Only students can create study groups.', 'danger')
        return redirect(url_for('group.list_groups'))

    form = GroupCreateForm()
    if form.validate_on_submit():
        group = Group(
            name=form.name.data.strip(),
            description=form.description.data.strip(),
            join_code=form.join_code.data.strip(),
            password=form.password.data.strip(),
            created_by=current_user.id,
            branch=current_user.branch,
            semester=current_user.semester
        )
        db.session.add(group)
        db.session.commit()

        membership = GroupMembership(
            user_id=current_user.id,
            group_id=group.id,
            name=current_user.name,
            roll_number=current_user.roll_number,
            branch=current_user.branch
        )
        db.session.add(membership)
        db.session.commit()

        flash('Group created and joined successfully!', 'success')
        return redirect(url_for('group.group_detail', group_id=group.id))

    return render_template('group/group_create.html', form=form)

@group_bp.route('/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = Group.query.get_or_404(group_id)

    if group.created_by != current_user.id:
        flash('You are not authorized to edit this group.', 'danger')
        return redirect(url_for('group.list_groups'))

    form = GroupCreateForm(obj=group)
    if form.validate_on_submit():
        group.name = form.name.data.strip()
        group.description = form.description.data.strip()
        group.join_code = form.join_code.data.strip()
        group.password = form.password.data.strip()
        db.session.commit()

        flash('Group updated successfully!', 'success')
        return redirect(url_for('group.group_detail', group_id=group.id))

    return render_template('group/group_create.html', form=form, edit_mode=True)

@group_bp.route('/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)

    if group.created_by != current_user.id:
        flash('You are not authorized to delete this group.', 'danger')
        return redirect(url_for('group.list_groups'))

    GroupMembership.query.filter_by(group_id=group.id).delete()
    GroupMessage.query.filter_by(group_id=group.id).delete()
    db.session.delete(group)
    db.session.commit()

    flash('Group deleted successfully.', 'success')
    return redirect(url_for('group.list_groups'))

@group_bp.route('/<int:group_id>/join', methods=['GET', 'POST'])
@login_required
def join_group(group_id):
    group = Group.query.get_or_404(group_id)

    # Already a member
    if GroupMembership.query.filter_by(user_id=current_user.id, group_id=group.id).first():
        flash('You are already a member of this group.', 'info')
        return redirect(url_for('group.group_detail', group_id=group.id))

    form = GroupJoinForm()

    if form.validate_on_submit():
        # Check credentials
        if form.code.data.strip() != group.join_code or form.password.data.strip() != group.password:
            flash('Invalid group code or password.', 'danger')
            return redirect(request.url)

        # Check member limit
        if GroupMembership.query.filter_by(group_id=group.id).count() >= 5:
            flash('This group is full. Maximum 5 members allowed.', 'warning')
            return redirect(url_for('group.list_groups'))

        # Restrict branch and semester
        if current_user.branch != group.branch or current_user.semester != group.semester:
            flash("You can only join groups of your own branch and semester.", "danger")
            return redirect(url_for('group.list_groups'))

        # Add to group
        membership = GroupMembership(
            user_id=current_user.id,
            group_id=group.id,
            name=form.name.data.strip(),
            roll_number=form.roll_number.data.strip(),
            branch=form.branch.data.strip()
        )
        db.session.add(membership)
        db.session.commit()

        flash(f'You joined "{group.name}" successfully!', 'success')
        return redirect(url_for('group.group_detail', group_id=group.id))

    return render_template('group/group_join.html', form=form, group=group)

@group_bp.route('/<int:group_id>', methods=['GET', 'POST'])
@login_required
def group_detail(group_id):
    group = Group.query.get_or_404(group_id)

    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group.id).first()
    if not membership:
        flash("You are not a member of this group.", "danger")
        return redirect(url_for('group.list_groups'))

    form = GroupMessageForm()
    if form.validate_on_submit():
        message = GroupMessage(
            content=form.content.data.strip(),
            user_id=current_user.id,
            group_id=group.id
        )
        db.session.add(message)
        db.session.commit()
        return redirect(url_for('group.group_detail', group_id=group.id))

    members = User.query.join(GroupMembership).filter(GroupMembership.group_id == group.id).all()
    messages = GroupMessage.query.filter_by(group_id=group.id).order_by(GroupMessage.timestamp.asc()).all()
    return render_template('group/group_detail.html', group=group, members=members, form=form, messages=messages)

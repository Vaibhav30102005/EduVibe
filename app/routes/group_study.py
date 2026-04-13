from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.forms.group_forms import (
    GroupCreateForm, GroupJoinForm, GroupMessageForm,
    EditGroupForm, DeleteGroupForm, LeaveGroupForm
)
from app.models import db, Group, GroupMembership, User, GroupMessage
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

group_bp = Blueprint('group_bp', __name__, url_prefix='/group')


# ✅ List user’s joined groups
@group_bp.route('/list', methods=['GET'])
@login_required
def list_groups():
    if current_user.role == 'admin':
        flash('Admins are not allowed to access study groups.', 'danger')
        return redirect(url_for('dashboard.index'))

    memberships = GroupMembership.query.filter_by(user_id=current_user.id).all()
    group_ids = [m.group_id for m in memberships]
    groups = Group.query.filter(Group.id.in_(group_ids)).all()

    return render_template('group/group_study.html', groups=groups)


# ✅ Create a new group
@group_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_group():
    if current_user.role not in ['student', 'cr']:
        flash('Only students or CRs can create groups.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = GroupCreateForm()
    if form.validate_on_submit():
        group_code = secrets.token_hex(4)
        hashed_password = generate_password_hash(form.group_password.data)

        group = Group(
            name=form.name.data,
            description=form.description.data,
            group_code=group_code,
            group_password=hashed_password,
            created_by=current_user.id,
            branch=current_user.branch,
            semester=current_user.semester
        )
        db.session.add(group)
        db.session.commit()

        member = GroupMembership(
            user_id=current_user.id,
            group_id=group.id,
            name=current_user.name,
            roll_number=current_user.roll_no,
            branch=current_user.branch
        )
        db.session.add(member)
        db.session.commit()

        flash('Group created successfully!', 'success')
        return redirect(url_for('group_bp.view_group', group_id=group.id))

    return render_template('group/create_group.html', form=form)


# ✅ Join a group
@group_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join_group():
    if current_user.role not in ['student', 'cr']:
        flash('Only students or CRs can join groups.', 'danger')
        return redirect(url_for('dashboard.index'))

    form = GroupJoinForm()
    if form.validate_on_submit():
        group = Group.query.filter_by(group_code=form.code.data).first()

        if not group:
            flash('Invalid group code.', 'danger')
            return render_template('group/join_group.html', form=form)

        if not check_password_hash(group.group_password, form.password.data):
            flash('Incorrect password.', 'danger')
            return render_template('group/join_group.html', form=form)

        if group.has_user_joined(current_user):
            flash('You are already a member of this group.', 'info')
            return redirect(url_for('group_bp.view_group', group_id=group.id))

        if not group.is_user_eligible(current_user):
            flash('You are not eligible to join this group (branch/semester mismatch).', 'warning')
            return render_template('group/join_group.html', form=form)

        if group.is_group_full():
            flash('This group is already full (5 members).', 'warning')
            return redirect(url_for('group_bp.view_group', group_id=group.id))

        new_member = GroupMembership(
            user_id=current_user.id,
            group_id=group.id,
            name=form.name.data,
            roll_number=form.roll_number.data,
            branch=form.branch.data
        )
        db.session.add(new_member)
        db.session.commit()

        flash('Successfully joined the group!', 'success')
        return redirect(url_for('group_bp.view_group', group_id=group.id))

    return render_template('group/join_group.html', form=form)


# ✅ View and interact with a group
@group_bp.route('/<int:group_id>', methods=['GET', 'POST'])
@login_required
def view_group(group_id):
    group = Group.query.get_or_404(group_id)

    if current_user.role == 'admin':
        flash('Admins are not allowed to access study groups.', 'danger')
        return redirect(url_for('dashboard.index'))

    is_creator = (group.created_by == current_user.id)
    is_member = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group.id).first() is not None
    can_interact = is_creator or is_member

    message_form = GroupMessageForm()
    if message_form.validate_on_submit() and can_interact:
        message = GroupMessage(
            user_id=current_user.id,
            group_id=group.id,
            content=message_form.content.data
        )
        db.session.add(message)
        db.session.commit()
        return redirect(url_for('group_bp.view_group', group_id=group.id))

    chat_messages = GroupMessage.query.filter_by(group_id=group.id).order_by(GroupMessage.timestamp.asc()).all()
    members = User.query.join(GroupMembership).filter(GroupMembership.group_id == group.id).all()

    delete_form = DeleteGroupForm()
    join_form = GroupJoinForm()
    leave_form = LeaveGroupForm()

    return render_template(
        'group/view_group.html',
        group=group,
        members=members,
        chat_messages=chat_messages,
        message_form=message_form,
        delete_form=delete_form,
        leave_form=leave_form,
        is_creator=is_creator,
        is_member=is_member,
        join_form=join_form
    )


# ✅ Edit group details
@group_bp.route('/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = Group.query.get_or_404(group_id)

    if group.created_by != current_user.id:
        flash('Only the creator can edit this group.', 'danger')
        return redirect(url_for('group_bp.view_group', group_id=group.id))

    form = EditGroupForm(obj=group)
    if form.validate_on_submit():
        group.name = form.name.data
        group.description = form.description.data
        db.session.commit()
        flash('Group updated successfully.', 'success')
        return redirect(url_for('group_bp.view_group', group_id=group.id))

    return render_template('group/create_group.html', form=form, is_edit=True)


# ✅ Delete a group
@group_bp.route('/<int:group_id>/delete', methods=['POST'])
@login_required
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)

    if group.created_by != current_user.id:
        flash('Only the creator can delete this group.', 'danger')
        return redirect(url_for('group_bp.view_group', group_id=group.id))

    GroupMembership.query.filter_by(group_id=group.id).delete()
    GroupMessage.query.filter_by(group_id=group.id).delete()
    db.session.delete(group)
    db.session.commit()

    flash('Group deleted successfully.', 'success')
    return redirect(url_for('group_bp.list_groups'))


# ✅ Leave group route
@group_bp.route('/<int:group_id>/leave', methods=['POST'])
@login_required
def leave_group(group_id):
    membership = GroupMembership.query.filter_by(user_id=current_user.id, group_id=group_id).first()
    if not membership:
        flash('You are not a member of this group.', 'danger')
        return redirect(url_for('group_bp.list_groups'))

    db.session.delete(membership)
    db.session.commit()

    flash('You have left the group.', 'info')
    return redirect(url_for('group_bp.list_groups'))

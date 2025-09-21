from pathlib import Path
import shutil
import datetime
import json
import uuid

from flask import request, flash
from flask import render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Regexp
from werkzeug.security import generate_password_hash

from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState
from obsiflask.utils import logger
from obsiflask.messages import add_message
from obsiflask.consts import DATE_FORMAT
from obsiflask.auth import get_db, login_perform, get_users, get_username_info, register_user, update_user, delete_user as delete_user_db
from flask_login import logout_user


def prettify_timedelta(td: datetime.timedelta):
    if td.days > 0:
        return f'{td.days} days ago'
    if td.seconds > 3600:
        return f'{td.seconds//3600} hours ago'
    if td.seconds > 60:
        return f'{td.seconds//60} minutes ago'
    return f'{td.seconds} seconds ago'


def check_vaults(vaults):
    vaults = json.loads(vaults)
    if not isinstance(vaults, list):
        raise ValueError('Vault list must be a list string')
    for v in vaults:
        if not isinstance(v, str):
            raise ValueError('Vault list must be a list string')
    for v in vaults:
        if v not in AppState.config.vaults:
            raise ValueError(f'Bad vault for user: {v}')


def gen_pass():
    return uuid.uuid4().hex


def drop_pass(current_user, target_user):
    try:
        if current_user['username'] == target_user:
            raise ValueError('Cannot drop the password of the current user')
        if current_user['username'] != AppState.config.auth.rootname:
            userinfo = get_username_info(target_user)
            if userinfo['is_root']:
                raise ValueError(
                    f'Ask {AppState.config.auth.rootname} to change the password of another administrator'
                )
        pwd = gen_pass()
        update_user(target_user, 'password_hash', generate_password_hash(pwd))
        flash(f'New password for {target_user} is "{pwd}"')

    except Exception as e:
        logger.warning(f'Bad action (drop password) in root panel: {e}')
        flash(repr(e), 'error')


def change_rights(current_user, target_user):
    try:
        if current_user['username'] == target_user:
            raise ValueError('Cannot change the rights of the current user')
        userinfo = get_username_info(target_user)
        if current_user['username'] != AppState.config.auth.rootname:
            userinfo = get_username_info(target_user)
            if userinfo['is_root']:
                raise ValueError(
                    f'Ask {AppState.config.auth.rootname} to change the rights of another administrator'
                )
        rights = 1 - userinfo['is_root']
        update_user(target_user, 'is_root', rights)
        flash(f'Changed rights for {target_user}')

    except Exception as e:
        logger.warning(f'Bad action (rights) in root panel: {e}')
        flash(repr(e), 'error')


def delete_user(current_user, target_user):
    try:
        if current_user['username'] == target_user:
            raise ValueError('Cannot delete current user')
        if current_user['username'] != AppState.config.auth.rootname:
            userinfo = get_username_info(target_user)
            if userinfo['is_root']:
                raise ValueError(
                    f'Ask {AppState.config.auth.rootname} to delete another administrator'
                )
        delete_user_db(target_user)
        flash(f'Dropped user {target_user} ')

    except Exception as e:
        logger.warning(f'Bad action (delete user) in root panel: {e}')

        flash(repr(e), 'error')


def change_vaults(current_user, target_user, vaultstr):
    try:
        if current_user['username'] != AppState.config.auth.rootname:
            userinfo = get_username_info(target_user)
            if userinfo['is_root'] and current_user['username'] != target_user:
                raise ValueError(
                    f'Ask {AppState.config.auth.rootname} to change the vaults of another administrator'
                )
        check_vaults(vaultstr)
        update_user(target_user, 'vaults', vaultstr)
        flash(f'Changed vaults for {target_user}')

    except Exception as e:
        logger.warning(f'Bad action (change vaults) in root panel: {e}')

        flash(repr(e), 'error')


class UserAddForm(FlaskForm):
    username = StringField(
        'User',
        validators=[
            DataRequired(),
            Regexp(
                "[a-z][a-z\-\_]*",
                message=
                "Only lowercased latin chars, _underscores_ and -dashes- are allowed. Must be started from latin char."
            )
        ])
    is_root = BooleanField('Super-user')
    vaults = StringField('Vaults (as a list)',
                         default="[]",
                         validators=[DataRequired()])
    ok = SubmitField('Create user')


def render_root() -> str:
    # since it must be secure, let's double check
    current_user = get_username_info()
    if not current_user['is_root']:
        return 401, "Not a root"
    form = UserAddForm()
    pwd = gen_pass()
    if form.validate_on_submit():
        try:
            check_vaults(form.vaults.data)
            register_user(form.username.data, pwd, form.vaults.data,
                          form.is_root.data)
            flash(
                f'The user {form.username.data} is successfully registered  with password: "{pwd}"'
            )
        except Exception as e:
            flash(f'Could not reigster a {form.username.data} user: {e}')
    else:
        op = request.args.get('op')
        user = request.args.get('user')
        if op is not None and user is not None:
            if op == 'pwd':
                drop_pass(current_user, user)
            elif op == 'rights':
                change_rights(current_user, user)
            elif op == 'delete':
                delete_user(current_user, user)
            elif op == 'vault':
                change_vaults(current_user, user, request.args.get('vaults'))

    return render_template('root.html', form=form, users=get_users())

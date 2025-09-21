from pathlib import Path
import shutil
import datetime

from flask import request, flash
from flask import render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, PasswordField
from wtforms.validators import DataRequired

from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState
from obsiflask.utils import logger
from obsiflask.messages import add_message
from obsiflask.consts import DATE_FORMAT
from obsiflask.auth import get_db, login_perform, update_user, get_user, generate_password_hash
from flask_login import logout_user


class ChangePassForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    repeat = PasswordField('Repeat Password', validators=[DataRequired()])
    change_pwd = SubmitField('Change password')


def change_pwd(form: ChangePassForm):
    if form.password.data != form.repeat.data:
        flash('Password doesn\"t match', "error")
        return
    try:
        update_user(get_user(), 'password_hash',
                    generate_password_hash(form.password.data))
        flash('Password succesfully changed')
    except Exception as e:
        flash(f'Could not change password: {e}', 'error')


def render_user() -> str:
    change_form = ChangePassForm()
    if change_form.validate_on_submit():
        change_pwd(change_form)
    return render_template('user.html', change_form=change_form)

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
from obsiflask.auth import get_db, login_perform
from flask_login import logout_user


class LoginForm(FlaskForm):
    username = StringField('User')
    password = PasswordField('Password')
    ok = SubmitField('Log in')


def render_login() -> str:
    form = LoginForm()
    back_url = url_for('index')
    if form.validate_on_submit():
        result = login_perform(form.username.data.lower(), form.password.data)
        if result:
            return redirect(back_url)
        else:
            flash('Could not log in', 'error')

    return render_template('login.html', form=form)


def render_logout():
    logout_user()
    return redirect(url_for("login"))

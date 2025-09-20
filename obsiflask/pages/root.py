from pathlib import Path
import shutil
import datetime

from flask import request, flash
from flask import render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired

from obsiflask.pages.index_tree import render_tree
from obsiflask.app_state import AppState
from obsiflask.utils import logger
from obsiflask.messages import add_message
from obsiflask.consts import DATE_FORMAT
from obsiflask.auth import get_db, login_perform, get_users, get_username_info
from flask_login import logout_user


class UserAddForm(FlaskForm):
    username = StringField('User')
    is_root = BooleanField('As root')
    vaults = StringField('Vaults (as a list)', default="[]")
    ok = SubmitField('Create user')


def render_root() -> str:
    # since it must be secure, let's double check
    if not get_username_info()['is_root']:
        return 401, "Not a root"
    form = UserAddForm()

    return render_template('root.html', form=form, users=get_users())

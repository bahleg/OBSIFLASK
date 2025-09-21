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


def render_sessions() -> str:
    # since it must be secure, let's double check

    formatted_session_hist = []
    for hist, v in AppState.session_tracker.items():
        dt = datetime.datetime.now() - v[1]
        formatted_session_hist.append({
            'user': hist[0],
            'address': hist[1],
            'details': v[0],
            'dt': prettify_timedelta(dt),
            'real_dt': dt
        })
    formatted_session_hist.sort(key=lambda x: x['real_dt'])
    return render_template('sessions.html', sessions=formatted_session_hist)

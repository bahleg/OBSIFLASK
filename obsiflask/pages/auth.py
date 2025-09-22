"""
Page processing logic for login and logout
"""
from flask import flash
from flask import render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import StringField, SubmitField, PasswordField

from obsiflask.auth import login_perform
from flask_login import logout_user


class LoginForm(FlaskForm):
    username = StringField('User', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
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

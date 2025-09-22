"""
Rendering logic for user settings
"""
from flask import request, flash
from flask import render_template
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired

from obsiflask.auth import update_user, get_user, generate_password_hash, get_user_config, save_user_config
from cmap import Colormap


class ChangePassForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    repeat = PasswordField('Repeat Password', validators=[DataRequired()])
    change_pwd = SubmitField('Change password')


BOOTSWATCH_THEMES = [
    'cerulean', 'cosmo', 'cyborg', 'darkly', 'flatly', 'journal', 'litera',
    'lumen', 'lux', 'materia', 'minty', 'pulse', 'sandstone', 'simplex',
    'sketchy', 'slate', 'solar', 'spacelab', 'superhero', 'united', 'yeti',
    'morph', 'quartz', 'vapor', 'zephyr'
]


class UserSettingForm(FlaskForm):
    bootstrap_theme = SelectField(
        'Bootswatch Theme',
        description=
        'For details please see <a href="https://bootswatch.com/">this link</a>',
        choices=BOOTSWATCH_THEMES,
        validators=[DataRequired()])
    contrast_dark = BooleanField(
        'Use contrast theme for dark mode',
        description="An adjustment for poorly-adapted light themes")
    contrast_light = BooleanField(
        'Use contrast theme for light mode',
        description="An adjustment for poorly-adapted dark themes")
    cmap = StringField(
        'Color map for graph visualization',
        description=
        'For details please see <a href="https://cmap-docs.readthedocs.io/en/stable/catalog/">this link</a>',
        validators=[DataRequired()])
    editor_preview = BooleanField(
        'Use editor preview in edit mode',
        description="Can be inconvenient for mobile usage")
    use_webgl = BooleanField(
        'Use WebGL for Graph Rendering',
        description=
        'It\'s recommended to enable it. Disable only if the graph rendering is not working.'
    )
    save_btn = SubmitField('Save settings')


def load_form_data(form: UserSettingForm):
    """
    Loads config into form
    """
    cfg = get_user_config()
    form.bootstrap_theme.data = cfg.bootstrap_theme.lower()
    form.contrast_dark.data = cfg.theme_contrast_dark
    form.contrast_light.data = cfg.theme_contrast_light
    form.cmap.data = cfg.graph_cmap
    form.editor_preview.data = cfg.editor_preview
    form.use_webgl.data = cfg.use_webgl


def save_settings(form: UserSettingForm):
    """
    Saves config
    """
    try:
        cfg = get_user_config()
        try:
            Colormap(form.cmap.data)
        except Exception as e:
            raise ValueError(f'Bad colormap: {e}')
        cfg.graph_cmap = form.cmap.data
        cfg.bootstrap_theme = form.bootstrap_theme.data
        cfg.editor_preview = form.editor_preview.data
        cfg.theme_contrast_dark = form.contrast_dark.data
        cfg.theme_contrast_light = form.contrast_light.data
        cfg.use_webgl = form.use_webgl.data
        save_user_config(get_user(), cfg)
        flash('User settings were saved')
    except Exception as e:
        flash(f'Problems with saving user settings: {e}', 'error')


def change_pwd(form: ChangePassForm):
    """
    Chagess password
    """
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
    user_form = UserSettingForm()
    if request.method == "GET":
        load_form_data(user_form)
    if "change_pwd" in request.form and change_form.validate_on_submit():
        change_pwd(change_form)
    if "save_btn" in request.form and user_form.validate_on_submit():
        save_settings(user_form)

    return render_template('user.html',
                           change_form=change_form,
                           user_form=user_form)

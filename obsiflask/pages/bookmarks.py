from threading import Lock
import json

from wtforms.fields import StringField, SubmitField, URLField
from wtforms.validators import DataRequired, Regexp
from flask_wtf import FlaskForm

from flask import render_template, request, flash

from obsiflask.app_state import AppState
from obsiflask.utils import resolve_service_path, logger

_lock = Lock()


class NewLinkForm(FlaskForm):
    alias = StringField(
        'Short name',
        validators=[
            DataRequired(),
            Regexp(
                "[a-z][a-z\-\_]*",
                message=
                "Only lowercased latin chars, _underscores_ and -dashes- are allowed. Must be started from latin char."
            )
        ])

    link = URLField('Full URL', validators=[
        DataRequired(),
    ])
    ok = SubmitField('Create link')


def load_links():
    path = resolve_service_path(AppState.config.shortlink_path)
    with _lock:
        if path.exists():
            with open(path) as inp:
                AppState.shortlinks = json.loads(inp.read())
        else:
            logger.info('Could not find any shortlink')
            for vault in AppState.config.vaults:
                AppState.shortlinks[vault] = {}


def add_and_save_links(vault: str, key: str, value: str | None):
    path = resolve_service_path(AppState.config.shortlink_path)
    with _lock:
        if value is not None:
            AppState.shortlinks[vault][key] = value
        else:
            del AppState.shortlinks[vault][key]
        with open(path, 'w') as out:
            out.write(json.dumps(AppState.shortlinks))


def render_links(vault):
    form = NewLinkForm()
    alias = AppState.config.vaults[vault].short_alias or vault
    if form.validate_on_submit():
        if form.alias.data in AppState.shortlinks[vault]:
            flash(f'Link {form.alias.data} already registered', 'error')
        else:
            add_and_save_links(vault, form.alias.data, form.link.data)
            flash(f'Link "{form.alias.data}" added')
    elif 'link' in request.args:
        key = request.args['link']
        if key not in AppState.shortlinks[vault]:
            flash(f'Link "{key}" not found', 'error')
        else:
            add_and_save_links(vault, key, None)
            flash(f'Link "{key}" deleted')

    return render_template('bookmarks.html',
                           form=form,
                           links=AppState.shortlinks[vault],
                           vault=vault,
                           alias=alias)

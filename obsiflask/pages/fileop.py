"""
The module provides a logic for the page with file/directory operations
"""

from pathlib import Path
import shutil
import datetime
from threading import Lock

from flask import request, abort
from flask import render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

from obsiflask.app_state import AppState
from obsiflask.utils import logger
from obsiflask.messages import add_message, type_to_int
from obsiflask.consts import DATE_FORMAT
from obsiflask.auth import get_user

lock = Lock()


class FileOpForm(FlaskForm):
    """
    A form to selecct operation
    """
    operation = SelectField('File operation',
                            choices=[('new', '📄 New file'),
                                     ('delete', '🗑️ Delete file'),
                                     ('copy', '🗐 Copy file'),
                                     ('move', '➜ Move file')])
    target = StringField('Target file', validators=[DataRequired()])
    """
    here target is the mfile to manipulate
    """
    template = SelectField('File type/Template to use',
                           choices=[('0_no', '📄 empty file'),
                                    ('1_dir', ('📁 New folder'))])
    destination = StringField('Destination')
    """
    the auxiliary field. used only for copy/move operations
    """
    ok = SubmitField()

    def __init__(self, vault, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vault = vault

    def validate(self, **kwargs):
        rv = FlaskForm.validate(self, **kwargs)  # checking fields at first
        if not rv:
            return False
        target = (AppState.indices[self.vault].path /
                  Path(self.target.data)).resolve()
        if not target.is_relative_to(AppState.indices[self.vault].path):
            self.target.errors.append(
                'Cannot manipulate file outside the vault')
            return False
        if self.operation.data == 'new':
            if target.exists():
                self.target.errors.append('File already exists')
                return False

        if self.operation.data in ['delete', 'copy', 'move']:
            if not target.exists():
                self.target.errors.append('File does not exist')
                return False

        if self.operation.data in ['copy', 'move']:
            dst = (AppState.indices[self.vault].path /
                   Path(self.destination.data)).resolve()
            if not dst.is_relative_to(AppState.indices[self.vault].path):
                self.destination.errors.append(
                    'Cannot manipulate file outside the vault')
                return False
            if target.is_dir() and (dst.exists() and not dst.is_dir()):
                self.destination.errors.append(
                    'Cannot copy/move directory to file')
                return False

        return True


def create_file_op(vault: str, form: FileOpForm) -> bool:
    """
    Creation of the file/folder operation

    Args:
        vault (str): vault name
        form (FileOpForm): form

    Returns:
        bool: True if success
    """

    try:
        path = AppState.indices[vault].path / Path(form.target.data)
        path.parent.mkdir(parents=True, exist_ok=True)
        if form.template.data.startswith('0_'):
            path.touch()
            AppState.hints[vault].update_file(form.target.data, get_user())
        elif form.template.data.startswith('1_'):
            path.mkdir(parents=True)
        else:
            template_name = form.template.data.split('_', 1)[1]
            found = False
            for t in AppState.indices[vault].get_templates():
                if str(t.name) == template_name:
                    found = True
                    break
            if not found:
                raise ValueError(f'could not find template {template_name}')
            with lock:
                shutil.copy(t, path)
        add_message(f'File {form.target.data} created',
                    0,
                    vault,
                    user=get_user())
        AppState.indices[vault].refresh()
        return True
    except Exception as e:
        add_message(f'Could not create file {form.target.data}',
                    type=2,
                    vault=vault,
                    details=repr(e),
                    user=get_user())
        return False


def delete_file_op(vault: str, form: FileOpForm, raise_exc: bool = False):
    """
    Delete file/folder operation

    Args:
        vault (str): vault name
        form (FileOpForm): form
    """
    try:
        path = AppState.indices[vault].path / Path(form.target.data)
        with lock:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        AppState.indices[vault].refresh()
        add_message(f'File {form.target.data} deleted',
                    0,
                    vault,
                    user=get_user())

    except Exception as e:
        if raise_exc:
            raise e
        add_message(f'Could not delete file {form.target.data}',
                    type=2,
                    vault=vault,
                    details=repr(e),
                    user=get_user())


def copy_move_file(vault: str, form: FileOpForm, copy: bool) -> bool:
    """
    Copy/Move operation

    Args:
        vault (str): vault name
        form (FileOpForm): form 
        copy (bool): if False, will perform move instead of copy

    Returns:
        bool: True on success
    """
    if copy:
        op_label = 'Copy'
    else:
        op_label = 'Move'
    try:
        path = AppState.indices[vault].path / Path(form.target.data)
        dst = AppState.indices[vault].path / Path(form.destination.data)
        with lock:
            if path.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
            if copy:
                if path.is_dir():
                    shutil.copytree(path, dst)
                else:
                    shutil.copy(path, dst)
                    AppState.hints[vault].update_file(form.destination.data,
                                                      get_user())
            else:
                shutil.move(path, dst)
                if not path.is_dir():
                    AppState.hints[vault].update_file(form.destination.data,
                                                      get_user())

        AppState.indices[vault].refresh()
        add_message(f'{op_label} {form.target.data}: successful',
                    0,
                    vault,
                    user=get_user())
        return True
    except Exception as e:
        logger.error(f'problem during file {op_label} {path.name}: {e}')
        add_message(f'Could not {op_label} file {form.target.data}',
                    type=2,
                    vault=vault,
                    details=repr(e),
                    user=get_user())
        return False


def render_fastop(vault: str) -> str:
    """
    A fast get-like API for file operations.
    All the arguments are got from url link

    Args:
        vault (str): vault name

    Returns:
        str: html redirect 
    """
    try:
        curfile = request.args.get('curfile')
        if curfile is None:
            curfile = request.args.get('curdir')

        if curfile is None:
            raise ValueError(f'target file not defined')
        op = request.args.get('op')
        if op not in ['copy', 'move', 'delete', 'file', 'folder', 'template']:
            raise ValueError(f'Bad operation: {op}')

        if op in ['copy', 'move', 'file', 'folder', 'template']:
            dst = request.args.get('dst')
            if dst is None:
                raise ValueError(
                    f'destination file for operation {op} is not defined')
        if op in ['template']:
            template = request.args.get('template')
            if template is None:
                raise ValueError(
                    f'template file for operation {op} is not defined')

        if op in ['file', 'folder']:
            if op == 'file':
                template = '0_no'
                route = 'editor'
            else:
                template = '1_dir'
                route = 'get_folder'

            form = FileOpForm(vault=vault,
                              operation='new',
                              target=curfile.rstrip('/') + '/' + dst,
                              template=template)
            if create_file_op(vault, form):
                return redirect(
                    url_for(route, vault=vault, subpath=form.target.data))
            else:
                raise ValueError(f'Could not create file/folder {dst}')

        if op == 'copy':
            form = FileOpForm(vault=vault,
                              operation='copy',
                              target=curfile,
                              destination=dst)
            if copy_move_file(vault, form, True):
                return redirect(
                    url_for('editor',
                            vault=vault,
                            subpath=form.destination.data))
            else:
                raise ValueError(
                    f'Could not perform copy from {curfile} to {dst}')
        if op == 'template':
            dst_real = curfile.rstrip('/') + '/' + dst
            form = FileOpForm(vault=vault,
                              operation='copy',
                              target=template,
                              destination=dst_real)
            if copy_move_file(vault, form, True):
                return redirect(
                    url_for('editor',
                            vault=vault,
                            subpath=form.destination.data))
            else:
                raise ValueError(
                    f'Could not perform copy from {template} to {dst_real}')
        if op == 'move':
            form = FileOpForm(vault=vault,
                              operation='move',
                              target=curfile,
                              destination=dst)
            if copy_move_file(vault, form, False):
                return redirect(
                    url_for('editor',
                            vault=vault,
                            subpath=form.destination.data))
            else:
                raise ValueError(
                    f'Could not perform move from {curfile} to {dst}')
        if op == 'delete':
            form = FileOpForm(vault=vault,
                              operation='delete',
                              target=curfile,
                              destination='')
            delete_file_op(vault, form, True)
            return 'ok'

    except Exception as e:
        add_message(
            'Exception during file operation',
            type_to_int['error'],
            vault,
            repr(e),
        )
        return abort(400)


def render_fileop(vault: str) -> str:
    """
    Rendering logic

    Args:
        vault (str): vault name

    Returns:
        str: Flask-rendered page
    """
    form = FileOpForm(vault)
    back_url = url_for('renderer_root', vault=vault)

    if request.method == "GET":
        if request.args.get('curfile'):
            form.target.data = request.args.get('curfile')
            back_url = url_for('renderer',
                               vault=vault,
                               subpath=request.args.get('curfile'))

        elif request.args.get('curdir'):
            back_url = url_for('get_folder',
                               vault=vault,
                               subpath=request.args.get('curdir'))
            form.target.data = request.args.get('curdir').rstrip(
                '/') + f'/{datetime.datetime.now().strftime(DATE_FORMAT)}.md'

        if request.args.get('curdir'):

            form.destination.data = request.args.get('curdir')
        else:
            form.destination.data = './'

    for t_id, t in enumerate(AppState.indices[vault].get_templates()):
        form.template.choices.append((f'{t_id+2}_{t.name}', f'📃 {t.name}'))

    if form.validate_on_submit():
        if form.operation.data == 'new':
            if create_file_op(vault, form):
                return redirect(
                    url_for('editor', vault=vault, subpath=form.target.data))
        if form.operation.data == 'delete':
            delete_file_op(vault, form)
        elif form.operation.data == 'copy':
            if copy_move_file(vault, form, True):
                return redirect(
                    url_for('editor',
                            vault=vault,
                            subpath=form.destination.data))

        elif form.operation.data == 'move':
            if copy_move_file(vault, form, False):
                return redirect(
                    url_for('editor',
                            vault=vault,
                            subpath=form.destination.data))
        return redirect(back_url)

    return render_template('fileop.html',
                           form=form,
                           home=AppState.config.vaults[vault].home_file,
                           vault=vault,
                           back_url=back_url)

"""
The module provides a logic for the page with file/directory operations
"""

from pathlib import Path
import shutil
from threading import Lock
import os

from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired

from obsiflask.app_state import AppState
from obsiflask.utils import logger
from obsiflask.messages import add_message
from obsiflask.auth import get_user
from obsiflask.utils import get_traceback
from obsiflask.obfuscate import obf_open
from obsiflask.consts import MAX_FILE_SIZE_MARKDOWN, TEXT_FILES_SFX

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
        self.target.description = f"""Use \"{AppState.config.vaults[vault].obfuscation_suffix}.md\" as a file suffix for obfuscated text. 
You can also add or remove  "{AppState.config.vaults[vault].obfuscation_suffix}\" suffix when copying/moving files to obfuscate-deobfuscate data."""

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
                    details=get_traceback(e),
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
                    details=get_traceback(e),
                    user=get_user())


def copy_move_file_op(in_: str | Path, out_: str | Path, vault: str,
                      copy: bool):
    """
    Performs a copy/move operation for files (not directories)
    w.r.t. to obfuscation

    Args:
        in_ (str | Path): in-file (can be obfuscated)
        out_ (str | Path): out-file (can be obfuscated)
        vault (str): vault name
        copy (bool): copy or move
    """
    in_ = Path(in_)
    out_ = Path(out_)
    if out_.is_dir():
        out_ = out_ / in_.name
    in_obf = AppState.config.vaults[vault].obfuscation_suffix in in_.suffixes
    out_obf = AppState.config.vaults[vault].obfuscation_suffix in out_.suffixes

    if in_obf == out_obf:
        if copy:
            shutil.copy(in_, out_)
        else:
            shutil.move(in_, out_)
    else:
        if os.path.getsize(in_) > MAX_FILE_SIZE_MARKDOWN:
            raise NotImplementedError(
                'Copy/move of obfscated/deobfuscated files is not supported yet'
            )
        if in_.suffix not in TEXT_FILES_SFX:
            b = 'b'
        else:
            b = ''

        with obf_open(in_, vault, 'r' + b) as inp:
            content = inp.read()
        with obf_open(out_, vault, 'w' + b) as out:
            out.write(content)
        if not copy:
            in_.unlink()


def copy_move_file(vault: str, form: FileOpForm, copy: bool) -> bool:
    """
    Copy/Move processing

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
                if dst.exists():
                    dst = dst / path.name
                dst.parent.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
            isdir = path.is_dir()
            if copy:
                copy_move_file_op(path, dst, vault, True)
                if isdir:
                    shutil.copytree(path, dst)
                else:
                    shutil.copy(path, dst)
                    AppState.hints[vault].update_file(form.destination.data,
                                                      get_user())
            else:
                if not isdir:
                    copy_move_file_op(path, dst, vault, False)
                    AppState.hints[vault].update_file(form.destination.data,
                                                      get_user())
                else:
                    shutil.move(path, dst)

        AppState.indices[vault].refresh()
        add_message(f'{op_label} {form.target.data}: successful',
                    0,
                    vault,
                    user=get_user())
        return True
    except Exception as e:
        logger.error(f'problem during file {op_label} {path.name}: {e}')
        add_message(
            f'Could not {op_label} file {form.target.data} to {form.destination.data}',
            type=2,
            vault=vault,
            details=get_traceback(e),
            user=get_user())
        return False

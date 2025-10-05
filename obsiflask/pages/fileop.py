"""
The module provides a logic for frontend handling for file operations
"""

import datetime
from pathlib import Path

from flask import request, abort
from flask import render_template, redirect, url_for
from werkzeug.utils import secure_filename

from obsiflask.auth import get_user
from obsiflask.app_state import AppState
from obsiflask.messages import add_message, type_to_int
from obsiflask.consts import DATE_FORMAT
from obsiflask.utils import get_traceback
from obsiflask.fileop import copy_move_file, create_file_op, delete_file_op, FileOpForm
from obsiflask.encrypt.obfuscate import obf_open
from obsiflask.consts import TEXT_FILES_SFX


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
        curfile_dir = False
        curfile = request.args.get('curfile')
        if curfile is None:
            curfile = request.args.get('curdir')
            curfile_dir = True
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

            # note: destination here is always local w.r.t. curfile
            if curfile_dir:
                dst = curfile.rstrip('/') + '/' + dst
            else:
                if '/' in curfile:
                    parent = curfile.rsplit('/', 1)[0]
                    dst = parent.rstrip('/') + '/' + dst

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
                              target=dst,
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
            form = FileOpForm(vault=vault,
                              operation='copy',
                              target=template,
                              destination=dst)
            if copy_move_file(vault, form, True):
                return redirect(
                    url_for('editor',
                            vault=vault,
                            subpath=form.destination.data))
            else:
                raise ValueError(
                    f'Could not perform copy from {template} to {dst}')
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
            get_traceback(e),
        )
        return abort(400)


def upload_files(vault: str, form: FileOpForm) -> bool:
    """
    Uploads files into the system

    Args:
        vault (str): vault name
        form (FileOpForm): form

    Returns:
        bool: if True, the uploading finished successfully
    """
    try:
        target = AppState.indices[vault].path / form.target.data
        target.parent.mkdir(parents=True, exist_ok=True)
        errors = []
        for f in form.files.data:
            fname = Path(f.filename)
            if not form.obfuscate.data:
                f.save(target / fname)
            else:
                if AppState.config.vaults[vault].obfuscation_suffix in Path(
                        fname).suffixes:
                    errors.append(
                        f'File {fname} already has an obfuscation. Skiping.')
                    continue
                bytes = f.read()
                fname = Path(fname).stem + AppState.config.vaults[
                    vault].obfuscation_suffix + Path(fname).suffix
                if Path(fname).suffix in TEXT_FILES_SFX:
                    content = bytes.decode('utf-8')
                    with obf_open(target / fname, vault, 'w') as out:
                        out.write(content)
                else:
                    with obf_open(target / fname, vault, 'wb') as out:
                        out.write(bytes)

        if len(errors) == 0:
            add_message(f'Files uploaded into {form.target.data}',
                        type_to_int['info'],
                        vault,
                        user=get_user())
        else:
            add_message(f'Files uploaded into {form.target.data} with errors',
                        type_to_int['warning'],
                        vault,
                        user=get_user(),
                        details='\n'.join(errors))
            return False
        return True
    except Exception as e:
        add_message(f'Error during files uploading: {e}',
                    type_to_int['error'],
                    vault,
                    get_traceback(e),
                    user=get_user())
        return False


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
        elif form.operation.data == 'upload':
            if upload_files(vault, form):
                return redirect(
                    url_for('get_folder',
                            vault=vault,
                            subpath=form.target.data))
        return redirect(back_url)

    return render_template('fileop.html',
                           form=form,
                           home=AppState.config.vaults[vault].home_file,
                           vault=vault,
                           back_url=back_url)

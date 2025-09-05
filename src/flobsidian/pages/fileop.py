from flask import abort, request
from pathlib import Path
from flask import render_template, redirect, url_for
from flobsidian.pages.renderer import get_markdown
from flobsidian.pages.index_tree import render_tree
from flobsidian.singleton import Singleton
from flobsidian.utils import logger
from flobsidian.messages import add_message
from flask import redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired
import shutil


class FileOpForm(FlaskForm):
    operation = SelectField('File operation',
                            choices=[('new', '📄 New file'),
                                     ('delete', '🗑️ Delete file'),
                                     ('copy', '🗐 Copy file'),
                                     ('move', '➜ Move file')])
    target = StringField('Target file', validators=[DataRequired()])
    template = SelectField('File type/Template to use',
                           choices=[('0_no', '📄 empty file'),
                                    ('1_dir', ('📁 New folder'))])
    destination = StringField('Destination')
    ok = SubmitField()

    def __init__(self, vault, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vault = vault

    def validate(self, **kwargs):
        rv = FlaskForm.validate(self, **kwargs)  # сначала проверяем все поля
        if not rv:
            return False
        target = (Singleton.indices[self.vault].path /
                  Path(self.target.data)).resolve()
        if not target.is_relative_to(Singleton.indices[self.vault].path):
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
            dst = (Singleton.indices[self.vault].path /
                   Path(self.destination.data)).resolve()
            if not dst.is_relative_to(Singleton.indices[self.vault].path):
                self.destination.errors.append(
                    'Cannot manipulate file outside the vault')
                return False
            if target.is_dir() and (dst.exists() and not dst.is_dir()):
                self.destination.errors.append(
                    'Cannot copy/move directory to file')
                return False

        return True


def create_file_op(vault, form: FileOpForm):
    try:
        path = Singleton.indices[vault].path / Path(form.target.data)
        path.parent.mkdir(parents=True, exist_ok=True)
        if form.template.data.startswith('0_'):
            path.touch()
        elif form.template.data.startswith('1_'):
            path.mkdir(parents=True)
        else:
            template_name = form.template.data.split('_', 1)[1]
            found = False
            for t in Singleton.indices[vault].get_templates():
                if str(t.name) == template_name:
                    found = True
                    break
            if not found:
                raise ValueError(f'could not find template {template_name}')
            shutil.copy(t, path)
        Singleton.indices[vault].add_file(path.resolve())
        add_message(f'File {form.target.data} created', 0, vault)
        return True
    except Exception as e:
        logger.error(f'problem during file creating {path.name}: {e}')
        add_message(f'Could not create file {form.target.data}',
                    type=2,
                    vault=vault,
                    details=repr(e))
        return False


def delete_file_op(vault, form: FileOpForm):
    try:
        path = Singleton.indices[vault].path / Path(form.target.data)
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()
        Singleton.indices[vault].refresh()
        add_message(f'File {form.target.data} deleted', 0, vault)

    except Exception as e:
        logger.error(f'problem during file deletion {path.name}: {e}')
        add_message(f'Could not delete file {form.target.data}',
                    type=2,
                    vault=vault,
                    details=repr(e))


def copy_move_file(vault, form: FileOpForm, copy):
    if copy:
        op_label = 'Copy'
    else:
        op_label = 'Move'
    try:
        path = Singleton.indices[vault].path / Path(form.target.data)
        dst = Singleton.indices[vault].path / Path(form.destination.data)
        if path.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
        if copy:
            if path.is_dir():
                shutil.copytree(path, dst)
            else:
                shutil.copy(path, dst)
        else:
            shutil.move(path, dst)

        Singleton.indices[vault].refresh()
        add_message(f'{op_label} {form.target.data}: successful', 0, vault)
        return True
    except Exception as e:
        logger.error(f'problem during file {op_label} {path.name}: {e}')
        add_message(f'Could not {op_label} file {form.target.data}',
                    type=2,
                    vault=vault,
                    details=repr(e))
        return False


def render_fileop(vault):
    navtree = render_tree(Singleton.indices[vault], vault, True)
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
                '/') + '/file.md'

        if request.args.get('curdir'):

            form.destination.data = request.args.get('curdir')
        else:
            form.destination.data = './'

    for t_id, t in enumerate(Singleton.indices[vault].get_templates()):
        form.template.choices.append((f'{t_id+1}_{t.name}', f'📃 {t.name}'))

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
                           navtree=navtree,
                           home=Singleton.config.vaults[vault].home_file,
                           vault=vault,
                           back_url=back_url)

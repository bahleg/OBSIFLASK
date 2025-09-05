from flask import abort
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

class FileOpForm(FlaskForm):
    operation = SelectField('File operation', choices=[('new', '📄 New file'), ('delete', '🗑️ Delete file'), ('copy', '🗐 Copy file'), ('move', '➜ Move file')])
    target = StringField('Target file', validators=[DataRequired()])
    template = SelectField('Template to use', choices=[('no', '× No template (empty file)')])
    destination = StringField('Destination')
    ok = SubmitField()






def create_file_op(vault, form: FileOpForm):
    try:
        path = Singleton.indices[vault].path/Path(form.target.data)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch()
        Singleton.indices[vault].add_file(path.resolve())
        add_message(f'File {form.target.data} created', 0, vault)
    except Exception as e:
        logger.error(f'problem during file creating {path}: {e}')
        add_message(f'Could not create file {form.target.data}', type=2, vault=vault, details=repr(e))



def delete_file_op(vault, form: FileOpForm):
    try:
        path = Singleton.indices[vault].path/Path(form.target.data)
        path.unlink()
        add_message(f'File {form.target.data} deleted', 0, vault)
    except Exception as e:
        logger.error(f'problem during file deleted {path}: {e}')
        add_message(f'Could not create file {form.target.data}', type=2, vault=vault, details=repr(e))


    
    


def render_fileop(vault):
    navtree = render_tree(Singleton.indices[vault], vault, True)
    form = FileOpForm()
    if form.validate_on_submit():
        if form.operation.data == 'new':
            create_file_op(vault, form)
        if form.operation.data == 'deleted':
            delete_file_op(vault, form)
        return redirect(url_for('renderer_root', vault=vault))
        
    return render_template('fileop.html',
                           form=form,
                           navtree=navtree,
            
                           home=Singleton.config.vaults[vault].home_file,
                           vault=vault)

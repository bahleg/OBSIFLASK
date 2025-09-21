import sqlite3
from pathlib import Path
import json
import uuid
from threading import Lock

import flask_login
from flask import Flask, g, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash

from obsiflask.utils import logger
from obsiflask.app_state import AppState

_lock = Lock()


class User(flask_login.UserMixin):

    def __init__(self, id: int, username, is_root):
        self.id = id
        self.username = username
        self.is_root = is_root


def get_db(create_ok: bool = False):
    try:
        if 'db' in g:
            return g.db
        context = True
    except:
        logger.warning(
            'probmes with context. It is expected when creating a db. Ignore it'
        )
        context = False
    exists = Path(AppState.config.auth.db_path).exists()
    if not exists:
        if not create_ok:
            raise ValueError(
                f'Could not find auth db: {AppState.config.auth.db_path}')
    db = sqlite3.connect(AppState.config.auth.db_path)
    db.row_factory = sqlite3.Row
    if context:
        g.db = db
    return db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def delete_user(username):
    db = get_db()
    with db:
        db.execute("DELETE from users WHERE username = ?", (username, ))


def update_user(username, field, value):
    assert field in ['password_hash', 'is_root', 'vaults']
    db = get_db()
    with _lock:
        with db:
            db.execute(f"UPDATE users SET {field} = ? WHERE username = ?",
                       (value, username))


def register_user(username: str, passwd: str, vaults: list[str], root=False):
    db = get_db(False)
    with _lock:
        user = db.execute('SELECT * FROM users WHERE username = ?',
                          (username, )).fetchone()
    if user:
        raise ValueError("user already exists")
    password_hash = generate_password_hash(passwd)
    root = int(root)
    with _lock:
        with db:
            db.execute(
                'INSERT INTO users (username, password_hash, is_root, vaults) VALUES (?, ?, ?, ?)',
                (username, password_hash, root, json.dumps(vaults)))


def try_create_db():
    exists = Path(AppState.config.auth.db_path).exists()
    if not exists:
        with _lock:
            db = get_db(True)
            db.row_factory = sqlite3.Row
            db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                vaults TEXT,
                is_root INTEGER NOT NULL DEFAULT 0
            )
            ''')
            db.commit()
        register_user(AppState.config.auth.rootname,
                      AppState.config.auth.default_root_pass,
                      list(AppState.config.vaults.keys()), True)


def get_username_info(username: str | None = None):
    if username is None:
        username = flask_login.current_user.username
    db = get_db()
    with _lock:
        user = db.execute('SELECT * FROM users WHERE username = ?',
                          (username, )).fetchone()
    return user


def get_users():
    db = get_db()
    with _lock:
        users = db.execute('SELECT * FROM users').fetchall()
    return list(map(dict, users))


def add_auth_to_app(app: Flask):
    if not AppState.config.auth.enabled:
        return
    secret = AppState.config.auth.secret
    if secret is None or len(secret.strip()) == '':
        logger.info('Generating secret')
        secret = uuid.uuid4().hex
    else:
        secret = secret.strip()
    app.secret_key = secret
    try_create_db()
    app.teardown_appcontext(close_db)
    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        db = get_db(False)
        with _lock:
            user = db.execute('SELECT * FROM users WHERE id = ?',
                              (user_id, )).fetchone()
        if user:
            return User(user['id'], user['username'], user['is_root'] != 0)
        else:
            logger.warning(f'an attempt to find user with id={user_id}')


def login_perform(username, passwd):
    db = get_db()
    with _lock:
        user = db.execute('SELECT * FROM users WHERE username = ?',
                          (username, )).fetchone()

    if user and check_password_hash(user['password_hash'], passwd):
        flask_login.login_user(User(user['id'], user['username'],
                                    user['is_root'] != 0),
                               remember=True)
        return True
    return False


def check_rights(
    vault: str | None,
    auth_enabled_required: bool = False,
    allow_non_auth: bool = False,
    root_required: bool = False,
    user_required: bool = True,
):
    if not AppState.config.auth.enabled:
        if auth_enabled_required:
            return "Only for authorized users", 401
        return None
    if not flask_login.current_user.is_authenticated:
        username = None
    else:
        username = flask_login.current_user.username
    if username is None and allow_non_auth:
        return None

    if username is None and user_required:
        return redirect(url_for('login'))

    if username is not None:
        username_info = get_username_info(username)
    else:
        username_info = None

    if username_info is None:
        raise ValueError(f'username {username} not found')
    if root_required and not username_info['is_root']:
        return "Only for root users", 403
    if not username_info['is_root'] and (vault is not None
                                         and vault not in json.loads(
                                             username_info['vaults'])):
        # the same as when the user entered non-existing vault
        # we don't want to show vaults of other users
        return "Bad vault", 400
    return None

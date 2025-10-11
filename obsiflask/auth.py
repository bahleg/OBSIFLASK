"""
Module for handling authentithication logic
"""
from dataclasses import dataclass
from copy import copy
import datetime
import sqlite3
from pathlib import Path
import json
from threading import Lock

from omegaconf import OmegaConf
import flask_login
from flask import Flask, g, redirect, url_for, request
from werkzeug.security import generate_password_hash, check_password_hash

from obsiflask.utils import logger, resolve_service_path
from obsiflask.app_state import AppState
from obsiflask.hint import HintIndex
from obsiflask.minihydra import load_config
from obsiflask.config import UserConfig

_lock = Lock()

MAX_SESSION_RECORDS = 100
"""
We track sessions and show them to the root user
"""


def save_user_config(user: str, config: UserConfig):
    """
    A helper to save user config

    Args:
        user (str): user name
        config (UserConfig): config to save
    """
    cfg_dir_path = resolve_service_path(Path(AppState.config.auth.user_config_dir))
    cfg_dir_path.mkdir(parents=True, exist_ok=True)
    cfg_path = cfg_dir_path / f'{user}.yml'
    OmegaConf.save(config, cfg_path)


def make_user_adjustments(user: str):
    """
    Make an application-specific adjustments, like creating a message list 
    for the pair "vault-user", etc

    Args:
        user (str): user name
    """
    for vault in AppState.hints:
        hi: HintIndex = AppState.hints[vault]
        hi.default_files_per_user[user] = copy(hi.default_files_per_user[None])
        AppState.messages[(vault, user)] = []
        cfg_dir_path = resolve_service_path(Path(AppState.config.auth.user_config_dir))
        cfg_path = cfg_dir_path / f'{user}.yml'
        config = None
        if cfg_path.exists():
            try:
                config = load_config(cfg_path, UserConfig)
            except Exception as e:
                logger.error(f'could not load config {cfg_path}: {e}')
        if config is None:
            config = copy(AppState.config.default_user_config)
            save_user_config(user, config)
        AppState.user_configs[user] = config


def make_user_vault_adjustment(user: str, vaults: list[str]):
    """Makes a vault-specific adjustment, 
    indicating for each vault if user is assigned to vault

    Args:
        user (str): user
        vaults (list[str]): list of vaults
    """
    vaults = set(vaults)
    for vault in AppState.users_per_vault:
        if vault in vaults:
            AppState.users_per_vault[vault].add(user)
        else:
            if user in AppState.users_per_vault[vault]:
                AppState.users_per_vault[vault].remove(user)


def get_user_config() -> UserConfig:
    """
    Gets user config or default if auth. is disabled
    Returns:
        UserConfig: config
    """
    if not AppState.config.auth.enabled or get_user() is None:
        return AppState.config.default_user_config
    else:
        return AppState.user_configs[get_user()]


class User(flask_login.UserMixin):
    """
    Flask-login object to represent user
    """

    def __init__(self, id: int, username: str, is_root: bool):
        self.id = id
        self.username = username
        self.is_root = is_root


def get_db(create_ok: bool = False) -> sqlite3.Connection:
    """
    Gets an auth. db connection

    Args:
        create_ok (bool, optional): if set, will try to create db. Defaults to False.

    Returns:
        sqlite3.Connection: connection to db
    """

    try:
        if 'db' in g:
            return g.db
        context = True
    except:
        logger.warning(
            'problems with context. It is expected when creating a db. Ignore it'
        )
        context = False
    path = resolve_service_path(AppState.config.auth.db_path)

    exists = path.exists()
    if not exists:
        if not create_ok:
            raise ValueError(f'Could not find auth db: {path}')
    db = sqlite3.connect(path)
    db.row_factory = sqlite3.Row
    if context:
        g.db = db
    return db


def close_db(e=None):
    """
    closes DB connection from flask session scope
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()


def delete_user(username: str):
    """
    Deletes user from db

    Args:
        username (str): user name
    """
    db = get_db()
    with db:
        db.execute("DELETE from users WHERE username = ?", (username, ))


def update_user(username: str, field: str, value):
    """
    Updates user

    Args:
        username (str): user name
        field (str): field name
        value: value to update
    """
    assert field in ['password_hash', 'is_root', 'vaults']
    db = get_db()
    with _lock:
        with db:
            db.execute(f"UPDATE users SET {field} = ? WHERE username = ?",
                       (value, username))
    if field == 'vaults':
        make_user_vault_adjustment(username, json.loads(value))


def register_user(username: str, passwd: str, vaults: list[str], root=False):
    """
    Creates new user

    Args:
        username (str): user name
        passwd (str): password
        vaults (list[str]): list of vaults
        root (bool, optional): super-user flag. Defaults to False.
    """
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
    make_user_adjustments(username)
    make_user_vault_adjustment(username, vaults)


def try_create_db():
    """
    Creates a new db with a root user
    """
    path = resolve_service_path(AppState.config.auth.db_path)
    exists = path.exists()
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
            db.execute(
                'CREATE UNIQUE INDEX idx_users_username ON users(username)')
            db.commit()
        register_user(AppState.config.auth.rootname,
                      AppState.config.auth.default_root_pass,
                      list(AppState.config.vaults.keys()), True)


def get_user() -> str | None:
    """
    Gets user name or None if auth. is disabled

    Returns:
        str | None: user name or None
    """

    if not AppState.config.auth.enabled:
        return None
    return flask_login.current_user.username


def get_username_info(username: str | None = None) -> dict[str, str]:
    """
    Gets user info from db

    Args:
        username (str | None, optional): user name. If not set, will user current user name.
          Defaults to None.

    Returns:
        dict[str, str]: db results
    """
    if username is None:
        username = get_user()
    db = get_db()
    with _lock:
        user = db.execute('SELECT * FROM users WHERE username = ?',
                          (username, )).fetchone()
    return user


def get_users() -> list[dict[str, str]]:
    """
    Retrieves all the users

    Returns:
        list[dict[str, str]]: db records for all the users
    """

    db = get_db()
    with _lock:
        users = db.execute('SELECT * FROM users').fetchall()
    return list(map(dict, users))


def add_auth_to_app(app: Flask):
    """
    Initializes auth. logic to app

    Args:
        app (Flask): flask application
    """
    if not AppState.config.auth.enabled:
        return
    app.config['SESSION_COOKIE_NAME'] = AppState.config.auth.session_cookie_name
    try_create_db()
    app.teardown_appcontext(close_db)
    login_manager = flask_login.LoginManager()
    login_manager.init_app(app)
    for user in get_users():
        make_user_adjustments(user['username'])
        make_user_vault_adjustment(user['username'],
                                   json.loads(user['vaults']))

    @login_manager.user_loader
    def load_user(user_id):
        """
        Helper for flask login manager
        """
        db = get_db(False)
        with _lock:
            user = db.execute('SELECT * FROM users WHERE id = ?',
                              (user_id, )).fetchone()
        if user:
            return User(user['id'], user['username'], user['is_root'] != 0)
        else:
            logger.warning(f'an attempt to find user with id={user_id}')


def login_perform(username: str, passwd: str) -> bool:
    """
    Performs login using username and password

    Args:
        username (str): username
        passwd (str): password

    Returns:
        bool: flag if login was successful
    """
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


def check_rights(vault: str | None,
                 auth_enabled_required: bool = False,
                 allow_non_auth: bool = False,
                 root_required: bool = False,
                 user_required: bool = True,
                 ignore_in_session_hist: bool = False):
    """
    Helper to check pages rights

    Args:
        vault (str | None): vault related to the page to chec
        auth_enabled_required (bool, optional): if set, requires enabeld auth. to show page. Defaults to False.
        allow_non_auth (bool, optional): if set, allows anonyms to user the page. Defaults to False.
        root_required (bool, optional): if set, only root users are allowed. Defaults to False.
        user_required (bool, optional): if set, users are allowed. Defaults to True.
        ignore_in_session_hist (bool, optional): if set, wont't add record to session history. Defaults to False.
    """
    if not AppState.config.auth.enabled:
        if auth_enabled_required:
            return "Only for authorized users", 401
        if AppState.config.auth.sessions_without_auth:
            add_session_record(None)
        return None
    if not flask_login.current_user.is_authenticated:
        username = None
    else:
        username = flask_login.current_user.username
    if username is None and allow_non_auth:
        if not ignore_in_session_hist:
            add_session_record(None)
        return None

    if username is None and user_required:
        return redirect(url_for('login'))

    if username is not None:
        username_info = get_username_info(username)
    else:
        username_info = None

    if username_info is None:
        raise ValueError(f'username {username} not found')
    if root_required and username_info['is_root'] == False:
        return "Only for root users", 403
    if not username_info['is_root'] and (vault is not None
                                         and vault not in json.loads(
                                             username_info['vaults'])):
        # the same as when the user entered non-existing vault
        # we don't want to show vaults of other users
        return "Bad vault", 400
    if not ignore_in_session_hist:
        add_session_record(username)
    return None


def add_session_record(user: str | None):
    """
    Adds a session history for the user

    Args:
        user (str | None): username or None if not registered
    """
    if not AppState.config.auth.enabled and not AppState.config.auth.sessions_without_auth:
        return
    if len(request.access_route) > 0:
        ip = request.access_route[0]
    else:
        ip = '?'
    key = (user, ip)
    ua_string = request.headers.get("User-Agent")
    AppState.session_tracker[key] = (ua_string, datetime.datetime.now())
    with _lock:
        if len(AppState.session_tracker) > 100:
            sorted_keys = sorted(AppState.session_tracker.items(),
                                 key=lambda x: x[1][-1],
                                 reverse=True)[MAX_SESSION_RECORDS:]
            for k in sorted_keys:
                del AppState.session_tracker[k[0]]

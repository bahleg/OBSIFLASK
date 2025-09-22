import pytest

from obsiflask.pages.user import load_form_data, save_settings, change_pwd, render_user, UserSettingForm, ChangePassForm
from obsiflask.main import run
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig, VaultConfig, AuthConfig, UserConfig
from obsiflask.auth import register_user, get_username_info, check_password_hash, login_perform


@pytest.fixture
def app(tmp_path):
    config = AppConfig(
        vaults={'vault1': VaultConfig(str(tmp_path))},
        auth=AuthConfig(enabled=True,
                        db_path=tmp_path / "db.db",
                        rootname="root",
                        default_root_pass="mypass",
                        user_config_dir=tmp_path / "users"),
    )
    app = run(config, True, True)
    return app


def test_load_form_data(app, monkeypatch):
    with app.test_request_context():
        monkeypatch.setattr('obsiflask.auth.get_user', lambda: 'root')
        form = UserSettingForm()
        load_form_data(form)
        assert AppState.user_configs['root'].bootstrap_theme.lower(
        ) == form.bootstrap_theme.data
        assert AppState.user_configs[
            'root'].editor_preview == form.editor_preview.data
        assert AppState.user_configs['root'].graph_cmap == form.cmap.data
        assert AppState.user_configs[
            'root'].theme_contrast_dark == form.contrast_dark.data
        assert AppState.user_configs[
            'root'].theme_contrast_light == form.contrast_light.data


def test_save_settings(app, monkeypatch):
    with app.test_request_context():
        monkeypatch.setattr('obsiflask.auth.get_user', lambda: 'root')
        form = UserSettingForm()
        form.bootstrap_theme.data = 'darkly'
        form.editor_preview.data = False
        form.cmap.data = 'colorbrewer:set2'
        form.contrast_dark.data = True
        form.contrast_light.data = True
        save_settings(form)

        monkeypatch.setattr('obsiflask.auth.get_user', lambda: 'root')
        form = UserSettingForm()
        load_form_data(form)
        assert AppState.user_configs['root'].bootstrap_theme.lower(
        ) == 'darkly'
        assert AppState.user_configs['root'].editor_preview == False
        assert AppState.user_configs['root'].graph_cmap == 'colorbrewer:set2'
        assert AppState.user_configs['root'].theme_contrast_dark == True
        assert AppState.user_configs['root'].theme_contrast_light == True


def test_change_pwd(app, monkeypatch):
    with app.test_request_context():
        assert login_perform('root', 'mypass')
        monkeypatch.setattr('obsiflask.auth.get_user', lambda: 'root')
        form = ChangePassForm()
        form.password.data = '123'
        form.repeat.data = '123'
        change_pwd(form)
        assert check_password_hash(
            get_username_info('root')['password_hash'], '123')


def test_render_user(app, monkeypatch):
    # only checking rendering with GET
    monkeypatch.setattr('obsiflask.auth.get_user', lambda: 'root')
    monkeypatch.setattr("obsiflask.pages.user.render_template",
                        lambda *a, **kw: {"rendered": kw})

    # checking only get
    with app.test_request_context():
        render_user()

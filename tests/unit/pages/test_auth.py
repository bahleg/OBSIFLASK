import pytest

from flask import url_for

from obsiflask.main import run
from obsiflask.config import AppConfig, VaultConfig, AuthConfig


@pytest.fixture
def app(tmp_path):

    config = AppConfig(
        vaults={'vault': VaultConfig(str(tmp_path))},
        auth=AuthConfig(enabled=True,
                        db_path=tmp_path / "db.db",
                        rootname="myroot",
                        default_root_pass="mypass",
                        user_config_dir=tmp_path / "users"),
    )
    app = run(config, True, True)
    return app


def test_login_success_and_redirect(app):
    with app.test_request_context():
        client = app.test_client()

        resp = client.post(
            "/login",
            data={
                "username": "myroot",
                "password": "mypass"
            },
            follow_redirects=False,
        )

        assert resp.status_code == 302
        assert resp.headers["Location"].endswith(url_for("index"))


def test_login_failure_shows_flash(app):
    with app.test_request_context():

        client = app.test_client()

        # неверный пароль
        resp = client.post(
            "/login",
            data={
                "username": "myroot",
                "password": "wrong"
            },
            follow_redirects=True,
        )

        assert resp.status_code == 200
        assert b"Could not log in" in resp.data


def test_logout_redirects_to_login(app):
    with app.test_request_context():

        client = app.test_client()

        client.post("/login",
                    data={
                        "username": "myroot",
                        "password": "mypass"
                    })

        resp = client.get("/logout", follow_redirects=False)

        assert resp.status_code == 302
        assert resp.headers["Location"].endswith(url_for("login"))

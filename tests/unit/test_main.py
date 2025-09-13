import pytest

from obsiflask.main import run
from obsiflask.app_state import AppState
from obsiflask.config import AppConfig

def test_app_runs():
    # Minimal config
    cfg = AppConfig(
        vaults={},
        flask_params={"testing": True}
    )
    app = run(cfg, True)
    client = app.test_client()
    response = client.get("/")
    
    # Проверяем что приложение отвечает 200 OK
    assert response.status_code == 200

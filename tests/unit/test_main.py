from obsiflask.main import run
from obsiflask.config import AppConfig

from obsiflask.observer import stop_observer
def test_app_runs():
    # Minimal config
    try:
        cfg = AppConfig(vaults={}, flask_params={"testing": True})
        app = run(cfg, True)
        client = app.test_client()
        response = client.get("/")

        # Проверяем что приложение отвечает 200 OK
        assert response.status_code == 200
    finally:
        stop_observer()
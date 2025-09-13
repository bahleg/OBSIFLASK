from flask import render_template
from obsiflask.app_state import AppState

def render_index():
    return render_template('index.html', vaults = AppState.config.vaults)
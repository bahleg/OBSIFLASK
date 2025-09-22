"""
A simple module with vault list
"""
import json

from flask import render_template
from obsiflask.app_state import AppState
from obsiflask.auth import get_username_info


def render_index():
    """
    Returns a list of vauls in rendered form
    """
    if not AppState.config.auth.enabled:
        vaults = AppState.config.vaults
    else:
        user = get_username_info()
        if user['is_root']:
            vaults = AppState.config.vaults
        else:
            vault_names = json.loads(user['vaults'])
            vaults = {k: AppState.config.vaults[k] for k in vault_names}
    return render_template('index.html', vaults=vaults)

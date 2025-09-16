"""
A simple module with vault list
"""
from flask import render_template
from obsiflask.app_state import AppState


def render_index():
    """
    Returns a list of vauls in rendered form
    """
    return render_template('index.html', vaults=AppState.config.vaults)

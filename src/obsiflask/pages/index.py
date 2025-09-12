from flask import render_template
from obsiflask.singleton import Singleton

def render_index():
    return render_template('index.html', vaults = Singleton.config.vaults)
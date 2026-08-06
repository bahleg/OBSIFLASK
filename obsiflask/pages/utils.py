"""
The module contains helpers for page rendering
"""
from pathlib import Path
from flask import redirect, url_for

from obsiflask.app_state import AppState


def check_vault(vault: str) -> tuple[str, int] | None:
    """
    Checks if the vault exists    

    Args:
        vault (str): vault name

    Returns:
        tuple[str, int] | None: flask-formatted return or None
    """
    cfg = AppState.config
    if vault not in cfg.vaults:
        return "Bad vault", 400
    return None


def resolve_path(vault: str, subpath: str) -> Path | tuple[str, int]:
    """
    Resolves path w.r.t. to application

    Args:
        vault (str): vault name
        subpath (str): path relative to vault

    Returns:
        Path | tuple[str, int]: flask-formatted return or absolute path 
    """
    vault_resolution_result = check_vault(vault)
    if vault_resolution_result is not None:
        return vault_resolution_result

    cfg = AppState.config
    real_path = (Path(cfg.vaults[vault].full_path) / subpath).resolve()
    if not real_path.exists():
        return f"Bad path: {subpath}", 400
    if not real_path.is_relative_to(
            Path(cfg.vaults[vault].full_path).resolve()):
        return f"Bad path: {subpath}", 400
    return real_path


def resolve_redirect_page(path: str, vault: str) -> str:
    """
    Guesses best redirect format for the file

    Args:
        path (str): path wrt vault
        vault (str): vault name

    Returns:
        str: name of the route to redirect
    """
    real_path = resolve_path(vault, path)
    if not isinstance(real_path, Path):
        # error
        return None 
    if not Path(real_path).exists():
        return None
    if Path(real_path).is_dir():
        return 'renderer'
    if path.endswith('.md'):
        return 'editor'
    else:
        return 'renderer'

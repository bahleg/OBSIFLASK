from dataclasses import dataclass, field


@dataclass
class UserConfig:
    pass


@dataclass
class VaultConfig:
    full_path: str
    allowed_users: list[str]
    home_file: str = ''


@dataclass
class Task:
    cmd: str
    interval: int
    vault: str
    success: str = 'Task finished successfully!'
    error: str = 'Task failed'


@dataclass
class AppConfig:
    vaults: dict[str, VaultConfig]
    tasks: list[Task] = field(default_factory=lambda: [])

    bootstrap_theme: str = "Solar"
    flask_params: dict = field(default_factory=lambda: {})
    log_path: str = './flobsidian.log'
    """
    Log level used for the project: [DEBUG, INFO, WARNING, ERROR]
    """
    log_level: str = 'DEBUG'

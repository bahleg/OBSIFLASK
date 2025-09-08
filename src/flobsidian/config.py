from dataclasses import dataclass, field


@dataclass
class UserConfig:
    pass



@dataclass
class BaseConfig:
    error_on_yaml_parse: bool = False
    error_on_field_parse: bool = False
    cache_time: int = 3600


@dataclass 
class GraphConfig:
    cache_time: int = 3600

@dataclass
class VaultConfig:
    full_path: str
    allowed_users: list[str]
    home_file: str = ''
    ignore_hidden_dirs: bool = True
    template_dir: str | None = None
    base_config: BaseConfig = field(default_factory=lambda: BaseConfig())
    graph_config : GraphConfig = field(default_factory=lambda: GraphConfig())

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
    

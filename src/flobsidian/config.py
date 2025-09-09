from dataclasses import dataclass, field


@dataclass
class UserConfig:
    use_webgl: bool = True
    bootstrap_theme: str = "Solar"
    default_graph_node_spacing: int = 4500
    default_graph_edge_length: int = 100
    default_graph_edge_stiffness: float = 0.45
    default_graph_compression: float = 1.0
    graph_cmap: str = 'colorbrewer:Set1'


@dataclass
class BaseConfig:
    error_on_yaml_parse: bool = False
    error_on_field_parse: bool = False
    cache_time: int = 3600


@dataclass
class GraphConfig:
    cache_time: int = 3600
    debug_graph: bool = False


@dataclass
class VaultConfig:
    full_path: str
    allowed_users: list[str]
    home_file: str = ''
    ignore_hidden_dirs: bool = True
    template_dir: str | None = None
    base_config: BaseConfig = field(default_factory=lambda: BaseConfig())
    graph_config: GraphConfig = field(default_factory=lambda: GraphConfig())


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
    flask_params: dict = field(default_factory=lambda: {})
    log_path: str = './flobsidian.log'
    default_user_config: UserConfig = field(
        default_factory=lambda: UserConfig())
    """
    Log level used for the project: [DEBUG, INFO, WARNING, ERROR]
    """
    log_level: str = 'DEBUG'

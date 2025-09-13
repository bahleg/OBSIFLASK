"""
Module describes configuration scheme.
For the main config class, see AppConfig
"""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class UserConfig:
    """
    User-specific config
    """
    use_webgl: bool = True
    """
    If true, will use webgl for graph rendering
    """
    bootstrap_theme: str = "Litera"
    """"
    Bootstrap theme from bootswatch
    """
    default_graph_node_spacing: int = 4500
    """
    Default value for node spacing parameter in graph rendering
    """
    default_graph_edge_length: int = 100
    """
    Default value for edge length parameter in graph rendering
    """
    default_graph_edge_stiffness: float = 0.45
    """
    Default value for edge stiffness parameter in graph rendering
    """
    default_graph_compression: float = 1.0
    """
    Default value for graph compression parameter in graph rendering
    """
    graph_cmap: str = 'colorbrewer:Set1'
    """
    Default colormap for graphs
    """


@dataclass
class BaseConfig:
    """
    Config for bases handling
    """
    error_on_yaml_parse: bool = False
    """
    If True, will raise an exception during bases yaml parsing.
    Otherwise, will put message and skip
    """
    error_on_field_parse: bool = False
    """
    If True, will raise an exception during formula parsing.
    Otherwise, will put message and skip
    """
    cache_time: int = 3600
    """
    Cache time in seconds. After that will rebuild the base render
    """


@dataclass
class GraphConfig:
    """
    Config for graph handling
    """
    cache_time: int = 3600
    """
    Cache time in seconds. After that will rebuild the graph
    """
    debug_graph: bool = False
    """
    If true, will render some debug info
    """
    fast_graph_max_nodes: int = 500
    """
    For graphs with larger node amount, will enable fast mode by default
    """
    fast_graph_max_edges: int = 50 * 49 // 2
    """
    For graphs with larger edge amount, will enable fast mode by default
    """
    louvain_communities_res: float = 1.0
    """
    Parameter for Louvain community detection algorithm
    """


@dataclass
class Task:
    """
    Task to execute inside the vault
    """
    cmd: str
    """
    Shell command
    """
    interval: int
    """
    Interval in second
    """
    success: str = 'Task finished successfully!'
    """
    Message for the success run
    """
    error: str = 'Task failed'
    """
    Message for the error run
    """


@dataclass
class VaultConfig:
    """
    Vault specific config
    """
    full_path: str
    """
    Path to vault directory. Can be local or absolute
    """
    home_file: str = ''
    """
    If set, clicking by the label on the sidebar will open the home file.
    Otherwise will open the directory
    """
    ignore_hidden_dirs: bool = True
    """
    If true, will ignore hidden files, like ".git"
    """
    template_dir: str | None = None
    """
    Optional directory to template files
    """
    base_config: BaseConfig = field(default_factory=BaseConfig)
    """
    Base handling config
    """
    graph_config: GraphConfig = field(default_factory=GraphConfig)
    """
    Graph handling config
    """
    tasks: list[Task] = field(default_factory=list)
    """
    List of tasks to be executed in the vault
    """
    title: str | None = None
    """
    Title for the vault index page.
    If not set, will show the key for the vault in the app config
    """
    short_title: str = ''
    """
    Short title for the sidebar and page title
    """
    description: str = ''
    """
    Description for the vault index page
    """
    file_index_update_time: int = 5 * 60
    """
    Cache time in seconds. After that will rebuild the file index
    """


@dataclass
class AppConfig:
    vaults: dict[str, VaultConfig]
    """
    Config for each vault
    """
    flask_params: dict[str, Any] = field(default_factory=dict)
    """
    Flask parameters. Will be put into app.run(**kwargs)
    """
    log_path: str = './obsiflask.log'
    """
    Path to save logs
    """
    default_user_config: UserConfig = field(default_factory=UserConfig)
    """
    User-specific config
    """
    log_level: str = 'DEBUG'
    """
    Log level used for the project: [DEBUG, INFO, WARNING, ERROR]
    """

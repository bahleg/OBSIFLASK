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

    use_webgl: bool = field(
        default=True,
        metadata={
            "help": "If true, will use webgl for graph rendering"
        },
    )

    bootstrap_theme: str = field(
        default="Litera",
        metadata={
            "help": "Bootstrap theme from bootswatch"
        },
    )

    theme_contrast_light: bool = field(
        default=False,
        metadata={
            "help": (
                "Some themes from bootswatch are not well adapted for light mode. "
                "For them we make an adjustment if set."
            )
        },
    )

    theme_contrast_dark: bool = field(
        default=False,
        metadata={
            "help": (
                "Some themes from bootswatch are not well adapted for dark mode. "
                "For them we make an adjustment if set."
            )
        },
    )

    graph_cmap: str = field(
        default="colorbrewer:Set1",
        metadata={
            "help": "Default colormap for graphs"
        },
    )

    editor_preview: bool = field(
        default=True,
        metadata={
            "help": "If disabled, will hide preview in the editor page"
        },
    )

@dataclass
class BaseConfig:
    """
    Config for bases handling
    """

    error_on_yaml_parse: bool = field(
        default=False,
        metadata={
            "help": (
                "If True, will raise an exception during bases yaml parsing. "
                "Otherwise, will put message and skip"
            )
        },
    )

    error_on_field_parse: bool = field(
        default=False,
        metadata={
            "help": (
                "If True, will raise an exception during formula parsing. "
                "Otherwise, will put message and skip"
            )
        },
    )

    cache_time: int = field(
        default=3600,
        metadata={
            "help": (
                "Cache time in seconds. After that will rebuild the base render"
            )
        },
    )



@dataclass
class GraphConfig:
    """
    Config for graph handling
    """

    cache_time: int = field(
        default=3600,
        metadata={
            "help": (
                "Cache time in seconds. After that will rebuild the graph"
            )
        },
    )

    debug_graph: bool = field(
        default=False,
        metadata={
            "help": "If true, will render some debug info"
        },
    )

    fast_graph_max_nodes: int = field(
        default=500,
        metadata={
            "help": (
                "For graphs with larger node amount, will enable fast mode by default"
            )
        },
    )

    fast_graph_max_edges: int = field(
        default=50 * 49 // 2,
        metadata={
            "help": (
                "For graphs with larger edge amount, will enable fast mode by default"
            )
        },
    )

    louvain_communities_res: float = field(
        default=1.0,
        metadata={
            "help": (
                "Parameter for Louvain community detection algorithm"
            )
        },
    )

    default_graph_node_spacing: int = field(
        default=4500,
        metadata={
            "help": (
                "Default value for node spacing parameter in graph rendering"
            )
        },
    )

    default_graph_edge_length: int = field(
        default=100,
        metadata={
            "help": (
                "Default value for edge length parameter in graph rendering"
            )
        },
    )

    default_graph_edge_stiffness: float = field(
        default=0.45,
        metadata={
            "help": (
                "Default value for edge stiffness parameter in graph rendering"
            )
        },
    )

    default_graph_compression: float = field(
        default=1.0,
        metadata={
            "help": (
                "Default value for graph compression parameter in graph rendering"
            )
        },
    )

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
    on_start: bool = False
    """
    If set, will run and then wait.
    Otherwise, will wait and then run.
    """


@dataclass
class VaultConfig:
    """
    Vault specific config
    """

    full_path: str = field(
        metadata={
            "help": "Path to vault directory. Can be local or absolute"
        },
    )

    short_alias: str | None = field(
        default=None,
        metadata={
            "help": "If set, will use short link for the short link pages"
        },
    )

    home_file: str = field(
        default="",
        metadata={
            "help": (
                "If set, clicking by the label on the sidebar will open the home file. "
                "Otherwise will open the directory"
            )
        },
    )

    ignore_hidden_dirs: bool = field(
        default=True,
        metadata={
            "help": 'If true, will ignore hidden files, like ".git"'
        },
    )

    template_dir: str | None = field(
        default=None,
        metadata={
            "help": "Optional directory to template files"
        },
    )

    base_config: BaseConfig = field(
        default_factory=BaseConfig,
        metadata={
            "help": "Base handling config"
        },
    )

    graph_config: GraphConfig = field(
        default_factory=GraphConfig,
        metadata={
            "help": "Graph handling config"
        },
    )

    tasks: list[Task] = field(
        default_factory=list,
        metadata={
            "help": "List of tasks to be executed in the vault"
        },
    )

    title: str | None = field(
        default=None,
        metadata={
            "help": (
                "Title for the vault index page. "
                "If not set, will show the key for the vault in the app config"
            )
        },
    )

    short_title: str | None = field(
        default=None,
        metadata={
            "help": "Short title for the sidebar and page title"
        },
    )

    description: str = field(
        default="",
        metadata={
            "help": "Description for the vault index page"
        },
    )

    file_index_update_time: int = field(
        default=5 * 60,
        metadata={
            "help": (
                "Cache time in seconds. After that will rebuild the file index"
            )
        },
    )

    message_list_size: int = field(
        default=100,
        metadata={
            "help": (
                "This amount of messages will be stored in the vault"
            )
        },
    )

    info_message_expiration: int = field(
        default=600,
        metadata={
            "help": (
                "The info messages won't popup if they were sent this amount of time in seconds"
            )
        },
    )

    message_fetch_time: int = field(
        default=1,
        metadata={
            "help": (
                "Take messages from server each message_fetch_time seconds"
            )
        },
    )

    message_fetch_limit: int = field(
        default=1,
        metadata={
            "help": "Take messages only N messages"
        },
    )

    autosave_time: int = field(
        default=10,
        metadata={
            "help": "Save documents each autosave_time seconds"
        },
    )

    autocomplete_max_ngrams: int = field(
        default=10000,
        metadata={
            "help": "Max ngrams to use in autocomplete"
        },
    )

    autocomplete_ngram_order: int = field(
        default=4,
        metadata={
            "help": "Ngram order to build an index in autocomplete"
        },
    )

    autocomplete_max_ratio_in_key: float = field(
        default=0.1,
        metadata={
            "help": "Remove frequent ngrams"
        },
    )

    obfuscation_key: str = field(
        default="abc",
        metadata={
            "help": (
                "This key is used to perform obfuscation of the markdown notes"
            )
        },
    )

    obfuscation_suffix: str = field(
        default=".obf",
        metadata={
            "help": (
                'The docs with the subsuffix (like ".obf.md") will be automatically '
                "obfuscate-deobfuscate"
            )
        },
    )

    max_files_to_upload: int = field(
        default=10,
        metadata={
            "help": "Maximum files to upload at one time"
        },
    )

    max_file_size_mb: int = field(
        default=10,
        metadata={
            "help": "File size of each file in mb"
        },
    )



@dataclass
@dataclass
class AuthConfig:
    """
    Class for multi-user regime
    """

    enabled: bool = field(
        default=False,
        metadata={
            "help": "If enabled, will use auth"
        },
    )

    db_path: str = field(
        default="./auth.db",
        metadata={
            "help": "Path to save auth database"
        },
    )

    rootname: str = field(
        default="root",
        metadata={
            "help": "The name for the root user"
        },
    )

    default_root_pass: str = field(
        default="${oc.env:OBSIFLASK_AUTH,'root'}",
        metadata={
            "help": "The initial password for the root user"
        },
    )

    sessions_without_auth: bool = field(
        default=False,
        metadata={
            "help": (
                'If set, will show "sessions" button even '
                "without enabled authentication"
            )
        },
    )

    user_config_dir: str = field(
        default="./user_cfg/",
        metadata={
            "help": "Path to save user configs"
        },
    )

    session_cookie_name: str = field(
        default="session",
        metadata={
            "help": "A cookie name for credential data storage"
        },
    )

@dataclass
class AppConfig:
    vaults: dict[str, VaultConfig] = field(
        metadata={
            "help": "Config for each vault"
        },
    )

    flask_params: dict[str, Any] = field(
        default_factory=dict,
        metadata={
            "help": "Flask parameters. Will be put into app.run(**kwargs)"
        },
    )

    log_path: str = field(
        default="./obsiflask.log",
        metadata={
            "help": "Path to save logs"
        },
    )

    default_user_config: UserConfig = field(
        default_factory=UserConfig,
        metadata={
            "help": "User-specific config"
        },
    )

    log_level: str = field(
        default="DEBUG",
        metadata={
            "help": (
                "Log level used for the project: [DEBUG, INFO, WARNING, ERROR]"
            )
        },
    )

    auth: AuthConfig = field(
        default_factory=AuthConfig,
        metadata={
            "help": "Multi-user settings"
        },
    )

    secret: str | None = field(
        default=None,
        metadata={
            "help": (
                "Flask app secret. If not set, will be generated at startup"
            )
        },
    )

    service_dir: str | None = field(
        default=None,
        metadata={
            "help": (
                "Directory to save service-specific files (auth databases, logs, etc). "
                "If not set, will ignore"
            )
        },
    )

    shortlink_path: str = field(
        default="shortlink_{}.json",
        metadata={
            "help": (
                "Path to save shortlink. Must contain '{}'"
            )
        },
    )

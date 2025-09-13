"""
Originally a code from embed2discover (https://gitlab.datascience.ch/democrasci/embed2discover)
GPLv3

The module mimics some features of Hydra library
"""
import sys
from typing import Optional, Any
from pathlib import Path
import importlib

from omegaconf import OmegaConf, DictConfig

TARGET_KEY = "_target_"
"""this key must contain the classpath to objects needed to create from the config"""


def load_config(path: str | Path, basic_type_dataclass=None) -> DictConfig:
    """
    Loads config from YAML.
    If basic_type_dataclass is provided, merges config with basic_type_dataclass 
    and validates results.

    Args:
    path (str| Path): path to YAML config
    basic_type_dataclass (dataclass): scheme, dataclass, defaults to None

    Returns:
        DictConfig: resulting config
    """
    if basic_type_dataclass is not None:
        scheme = OmegaConf.structured(basic_type_dataclass)
    config = OmegaConf.load(path)
    if basic_type_dataclass is not None:
        config = OmegaConf.merge(scheme, config)

    return config


def load_entrypoint_config(basic_type_dataclass=None) -> DictConfig:
    """
    A very basic handler for CLI.
    Validates that there is given only one argument, convverts it into config.

    Args:
        basic_type_dataclass (dataclass): optional dataclass for scheme validation, defaults to None
        ext_cfg_key (str|None): if set, will extend configs from the file listed in config entry with this key
        ext_dir_key (str|None): if set, will extend configs from the directories listed in config entry with this key

    Returns:
        DictConfig: loaded config from CLI argument
    """
    assert len(
        sys.argv) == 2, "Script allows only one argument: path to YML config"
    config = load_config(sys.argv[1], basic_type_dataclass)
    return config


def init(init_dict: dict, required_type: Optional[type] = None) -> Any:
    """
    Initializes an object from config.

    Args:
        init_dict (Dict): dict with data to initalize.
        The dict must contain _target_ key with full python classpath.
        The dict can contain other arguments that needed to init recursively
    
        required_type (type | None): optional type to validate, defaults to None

    Returns:
        Any: new object created from config
    """
    assert TARGET_KEY in init_dict, f"{TARGET_KEY} not found in dict: {init_dict}"
    class_path = init_dict[TARGET_KEY]
    module = importlib.import_module(class_path.rsplit(".", 1)[0])
    classtype = getattr(module, class_path.split(".")[-1])
    kwargs = {k: v for k, v in init_dict.items() if k != TARGET_KEY}
    for k in kwargs:
        if isinstance(kwargs[k], DictConfig) or isinstance(kwargs[k], dict):
            if TARGET_KEY in kwargs[k].keys():
                kwargs[k] = init(kwargs[k])

    result = classtype(**kwargs)
    if required_type is not None:
        assert isinstance(
            result, required_type
        ), f"Initialized objects of type {type(result)} is not instance of required type {required_type}"
    return result

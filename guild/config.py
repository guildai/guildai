import errno
import os

import yaml

import guild.var

def load_config():
    try:
        f = open(config_source_path(), "r")
    except IOError as e:
        if e.errno != errno.ENOENT:
            raise
        return {}
    else:
        with f:
            return yaml.load(f)

def config_source_path():
    return guild.var.path("config.yml")

def write_config(config):
    filename = config_source_path()
    _ensure_dir(filename)
    with open(filename, "w") as f:
        yaml.dump(config, f, default_flow_style=False, indent=2)

def _ensure_dir(filename):
    try:
        os.makedirs(os.path.dirname(filename))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

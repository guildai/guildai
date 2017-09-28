import yaml

import guild.var

def sources():
    return load_config().get("package-sources", [])

def load_config():
    with open(config_source_path(), "r") as f:
        return yaml.load(f)

def config_source_path():
    return guild.var.path("config.yml")

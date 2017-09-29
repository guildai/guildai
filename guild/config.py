import errno
import os

import yaml

import guild.var

class SourceExistsError(KeyError):
    pass

class SourceNameError(KeyError):
    pass

def sources():
    return load_config().get("package-sources", [])

def load_config():
    with open(config_source_path(), "r") as f:
        return yaml.load(f)

def config_source_path():
    return guild.var.path("config.yml")

def add_source(name, url):
    config = load_config()
    sources = config.get("package-sources", [])
    _verify_source_not_exists(name, sources)
    sources.append({"name": name, "url": url})
    write_config(config)

def remove_source(name):
    config = load_config()
    sources = config.get("package-sources", [])
    for source in sources:
        if source.get("name") == name:
            sources.remove(source)
            break
    else:
        raise SourceNameError(name)
    write_config(config)

def _verify_source_not_exists(name, sources):
    for source in sources:
        if source.get("name") == name:
            raise SourceExistsError(name)

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

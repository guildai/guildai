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

def add_source(name, source):
    config = load_config()
    sources = config.setdefault("package-sources", [])
    _verify_source_not_exists(name, sources)
    sources.append({"name": name, "source": source})
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

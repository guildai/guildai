#!/usr/bin/env python

# Copyright 2017 TensorHub, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys

import yaml

# Change every time venv caching scheme changes
cache_scheme_version = 3

targets = {
    "linux-python-2.7": {
        "image": "circleci/python:2.7-node-browsers",
        "python": "python2.7",
    },

    "linux-python-3.5": {
        "image": "circleci/python:3.5-node-browsers",
        "python": "python3.5",
    },

    "linux-python-3.6": {
        "image": "circleci/python:3.6-node-browsers",
        "python": "python3.6",
    }
}

def main():
    config = _render_config()
    with open("config.yml", "w") as out:
        yaml.dump(config, out, default_flow_style=False, width=9999)

def _render_config():
    return {
        "version": 2,
        "jobs": _jobs(),
        "workflows": _workflows()
    }

def _jobs():
    return {
        name: _job(name, config)
        for name, config in targets.items()
    }

def _job(name, config):
    return {
        "docker": _docker(config),
        "working_directory": "~/repo",
        "steps": _default_steps(name, config)
    }

def _docker(config):
    return [{"image": config["image"]}]

def _default_steps(name, config):
    return [
        "checkout",
        _restore_cache(name),
        _install_deps(config),
        _save_cache(name),
        _build(),
        _test(),
        _store_artifacts(),
        _upload_to_pypi(),
    ]

def _restore_cache(name):
    return {
        "restore_cache": {
            "keys": [_cache_key(name)]
        }
    }

def _cache_key(name):
    return (
        "%s-%i-{{ checksum \"requirements.txt\" }}"
        "-{{ checksum \"guild/view/package.json\" }}"
        % (name, cache_scheme_version))

def _install_deps(config):
    return _run(
        "Install dependencies", [
            "virtualenv venv --python %s" % config["python"],
            "source venv/bin/activate",
            "pip install -r requirements.txt",
            "pip install tensorflow",
            "cd guild/view && npm install",
        ])

def _run(name, cmd_lines):
    return {
        "run": {
            "name": name,
            "command": "\n".join(cmd_lines)
        }
    }

def _save_cache(name):
    return {
        "save_cache": {
            "paths": ["venv"],
            "key": _cache_key(name)
        }
    }

def _build():
    return _run(
        "Build", [
            "source venv/bin/activate",
            "python setup.py bdist_wheel -p manylinux1_x86_64",
        ])

def _test():
    return _run(
        "Test", [
            "source venv/bin/activate",
            "guild/scripts/guild check -nT",
        ])

def _store_artifacts():
    return {
        "store_artifacts": {
            "path": "dist",
            "destination": "dist"
        }
    }

def _upload_to_pypi():
    return _run(
        "Upload to PyPI", [
            "source venv/bin/activate",
            "twine upload --skip-existing dist/*.whl",
        ])

def _workflows():
    return {
        "version": 2,
        "all": {
            "jobs": [_workflow_job(name) for name in targets]
        }
    }

def _workflow_job(name):
    return {
        name: {
            "filters": {
                "branches": {
                    "only": "release"
                }
            }
        }
    }

if __name__ == "__main__":
    main()

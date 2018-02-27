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

import yaml

class Build(object):

    name = None
    python = None
    env = None

    skip_tests = []

    # Increment when caching scheme changes
    cache_scheme_version = 5

    cache_dep_files = [
        "requirements.txt",
        "guild/view/package.json",
    ]

    def job(self):
        assert self.env
        return {
            self.env: self.env_config(),
            "working_directory": "~/repo",
            "steps": self.steps()
        }

    def steps(self):
        return [
            self.checkout(),
            self.restore_cache(),
            self.install_deps(),
            self.save_cache(),
            self.build(),
            self.test(),
            self.store_artifacts(),
            self.upload_to_pypi(),
        ]

    def install_deps(self):
        return self._run("Install dependencies", self._install_deps_lines())

    def _install_deps_lines(self):
        return [
            self.init_venv(),
            "source venv/bin/activate",
            "pip install -r requirements.txt",
            "pip install tensorflow",
            "cd guild/view && npm install",
        ]

    def init_venv(self):
        assert self.python
        if self.python.startswith("3."):
            return "python -m venv venv"
        else:
            return "virtualenv venv"

    @staticmethod
    def checkout():
        return "checkout"

    def restore_cache(self):
        return {
            "restore_cache": {
                "keys": [self.cache_key()]
            }
        }

    def cache_key(self):
        assert self.name
        checksums = "-".join(
            ["{{ checksum '%s' }}" % path for path in self.cache_dep_files]
        )
        return "%s-%i-%s" % (self.name, self.cache_scheme_version, checksums)

    def save_cache(self):
        return {
            "save_cache": {
                "paths": ["venv"],
                "key": self.cache_key()
            }
        }

    def build(self):
        return self._run(
            "Build", [
                "source venv/bin/activate",
                self._bdist_wheel_cmd(),
            ])

    @staticmethod
    def _bdist_wheel_cmd():
        return "python setup.py bdist_wheel"

    def test(self):
        skip_tests = "".join([" --skip %s" % t for t in self.skip_tests])
        return self._run(
            "Test", [
                "source venv/bin/activate",
                "guild/scripts/guild check -T%s" % skip_tests,
            ])

    @staticmethod
    def store_artifacts():
        return {
            "store_artifacts": {
                "path": "dist",
                "destination": "dist"
            }
        }

    def upload_to_pypi(self):
        return self._run(
            "Upload to PyPI", [
                "source venv/bin/activate",
                "twine upload --skip-existing dist/*.whl",
            ])

    @staticmethod
    def _run(name, cmd_lines):
        return {
            "run": {
                "name": name,
                "command": "\n".join(cmd_lines)
            }
        }

    def workflow_job(self):
        return {
            self.name: {
                "filters": {
                    "branches": {
                        "only": "release"
                    }
                }
            }
        }

class LinuxBuild(Build):

    env = "docker"

    images = {
        "linux-python-2.7": "circleci/python:2.7-stretch-node",
        "linux-python-3.5": "circleci/python:3.5-jessie-node",
        "linux-python-3.6": "circleci/python:3.6-stretch-node",
    }

    skip_tests = ["tables"]

    def __init__(self, python):
        self.python = python
        self.name = "linux-python-%s" % python

    def env_config(self):
        return [{"image": self.images[self.name]}]

    @staticmethod
    def _bdist_wheel_cmd():
        return "python setup.py bdist_wheel -p manylinux1_x86_64"

class MacBuild(Build):

    env = "macos"

    xcode_version = "9.2.0"

    def __init__(self, python):
        self.python = python
        self.name = "macos-python-%s" % python

    def env_config(self):
        return {
            "xcode": self.xcode_version
        }

    def _install_deps_lines(self):
        lines = super(MacBuild, self)._install_deps_lines()
        if self.python == "3.6":
            lines.append("brew install python3")
        else:
            assert self.python == "2.7", self.python
        return lines

class Config(object):

    version = 2

    def __init__(self, builds):
        self.builds = builds

    def write(self):
        config = {
            "version": 2,
            "jobs": self._jobs(),
            "workflows": self._workflows()
        }
        with open("config.yml", "w") as out:
            yaml.dump(config, out, default_flow_style=False, width=9999)

    def _jobs(self):
        return {
            build.name: build.job() for build in self.builds
        }

    def _workflows(self):
        return {
            "version": self.version,
            "all": {
                "jobs": [build.workflow_job() for build in self.builds]
            }
        }

builds = [
    #LinuxBuild(python="2.7"),
    #LinuxBuild(python="3.5"),
    #LinuxBuild(python="3.6"),
    MacBuild(python="2.7"),
    #MacBuild(python="3.6"),
]

def main():
    config = Config(builds)
    config.write()

if __name__ == "__main__":
    main()

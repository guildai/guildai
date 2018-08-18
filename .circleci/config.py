#!/usr/bin/env python

# Copyright 2017-2018 TensorHub, Inc.
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

    cache_scheme_version = 13

    name = None
    python = None
    env = None

    pip = "pip"

    build_dir = "build-env"
    test_dir = "test-env"

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
            self.install_build_deps(),
            self.save_cache(),
            self.build(),
            self.install_dist(),
            self.test(),
            self.store_artifacts(),
            self.upload_to_pypi(),
        ]

    @staticmethod
    def checkout():
        return "checkout"

    def restore_cache(self):
        return {
            "restore_cache": {
                "keys": [self._cache_key()]
            }
        }

    def _cache_key(self):
        assert self.name
        checksums = "-".join(
            ["{{ checksum \"%s\" }}" % path for path in self.cache_dep_files]
        )
        return "%s-%i-%s" % (self.name, self.cache_scheme_version, checksums)

    def install_build_deps(self):
        return self._run(
            "Install build dependencies",
            self._install_build_deps_cmd())

    def _install_build_deps_cmd(self):
        return [
            self._ensure_virtual_env_cmd(),
            self._init_env(self.build_dir),
            self._activate_env(self.build_dir),
            self._upgrade_pip(),
            self._install_guild_reqs(),
            self._install_tensorflow(),
            self._install_guild_view_reqs(),
        ]

    def _ensure_virtual_env_cmd(self):
        return "sudo {} install --upgrade virtualenv".format(self.pip)

    @staticmethod
    def _init_env(path):
        return (
            "test -e {path}/bin/activate || virtualenv {path}"
            .format(path=path))

    @staticmethod
    def _activate_env(path):
        return ". %s/bin/activate" % path

    def _upgrade_pip(self):
        # pipe to cat here effectively disables progress bar
        return "{pip} install --upgrade {pip} | cat".format(pip=self.pip)

    def _install_guild_reqs(self):
        # pipe to cat here effectively disables progress bar
        return "{} install -r requirements.txt | cat".format(self.pip)

    def _install_tensorflow(self):
        return "{} install grpcio==1.9.1 tensorflow".format(self.pip)

    @staticmethod
    def _install_guild_view_reqs():
        return "cd guild/view && npm install"

    def save_cache(self):
        return {
            "save_cache": {
                "paths": [self.build_dir],
                "key": self._cache_key()
            }
        }

    def build(self):
        return self._run(
            "Build", [
                ". %s/bin/activate" % self.build_dir,
                self._bdist_wheel_cmd(),
            ])

    @staticmethod
    def _bdist_wheel_cmd():
        return "python setup.py bdist_wheel"

    def install_dist(self):
        return self._run("Install dist", [
            "sudo {} install dist/*.whl".format(self.pip),
        ])

    def test(self):
        return self._run("Test", [
            ("guild init2 -y"
             " --no-progress"
             " --name guild-test"
             " --guild dist/*.whl {}".format(self.test_dir)),
            "TERM=xterm-256color source guild-env {}".format(self.test_dir),
            "WORKSPACE={} guild check --uat".format(self.test_dir),
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
                self._activate_env(self.build_dir),
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
        if self.python.startswith("3."):
            self.pip = "pip3"

    def env_config(self):
        return {
            "xcode": self.xcode_version
        }

    def _install_build_deps_cmd(self):
        lines = super(MacBuild, self)._install_build_deps_cmd()
        if self.python.startswith("3."):
            lines[:0] = [
                "brew upgrade python > /dev/null",
            ]
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
    LinuxBuild(python="2.7"),
    LinuxBuild(python="3.5"),
    LinuxBuild(python="3.6"),
    MacBuild(python="2.7"),
    MacBuild(python="3.6"),
]

def main():
    config = Config(builds)
    config.write()

if __name__ == "__main__":
    main()

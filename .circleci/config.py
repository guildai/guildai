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

class WorkflowJob(object):

    def job(self):
        raise NotImplementedError()

    def workflow_job(self):
        raise NotImplementedError()

def run(name, cmd_lines):
    return {
        "run": {
            "name": name,
            "command": "\n".join(cmd_lines)
        }
    }

class Build(WorkflowJob):

    cache_scheme_version = 10

    name = None
    env = None
    python = None

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
            self.install_deps(),
            self.save_cache(),
            self.build(),
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

    def install_deps(self):
        return run("Install dependencies", self._install_deps_cmd())

    def _install_deps_cmd(self):
        return [
            self._ensure_virtual_env_cmd(),
            self._init_env(self.build_dir),
            self._activate_env(self.build_dir),
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
        return run(
            "Build", [
                ". %s/bin/activate" % self.build_dir,
                self._bdist_wheel_cmd(),
            ])

    @staticmethod
    def _bdist_wheel_cmd():
        return "python setup.py bdist_wheel"

    def test(self):
        return run("Test", [
            self._init_env(self.test_dir),
            self._activate_env(self.test_dir),
            "{} install dist/*.whl".format(self.pip),
            "WORKSPACE=%s guild check --uat" % self.test_dir,
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
        return run(
            "Upload to PyPI", [
                self._activate_env(self.build_dir),
                "twine upload --skip-existing dist/*.whl",
            ])

    def workflow_job(self):
        assert self.name
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
        self.name = "build-linux-python-%s" % python
        self.python = python

    def env_config(self):
        return [{"image": self.images[self.name]}]

    @staticmethod
    def _bdist_wheel_cmd():
        return "python setup.py bdist_wheel -p manylinux1_x86_64"

class MacBuild(Build):

    env = "macos"
    xcode_version = "9.2.0"

    def __init__(self, python):
        self.name = "build-macos-python-%s" % python
        self.python = python
        if self.python.startswith("3."):
            self.pip = "pip3"

    def env_config(self):
        return {
            "xcode": self.xcode_version
        }

    def _install_deps_cmd(self):
        lines = super(MacBuild, self)._install_deps_cmd()
        if self.python.startswith("3."):
            lines[:0] = [
                "brew upgrade python > /dev/null",
            ]
        return lines

class ReleaseUAT(WorkflowJob):

    name = None
    env = None
    python = None

    def job(self):
        assert self.env
        return {
            self.env: self.env_config(),
            "working_directory": "~",
            "steps": self.steps()
        }

    def steps(self):
        return [
            self.init_env(),
            self.install_guild(),
            self.init_guild(),
            self.uat(),
        ]

    def init_env(self):
        return run("Init env", self._init_env_cmd())

    @staticmethod
    def _init_env_cmd():
        return ["which pip"]

    def install_guild(self):
        return run("Install Guild", self._install_guild_cmd())

    @staticmethod
    def _install_guild_cmd():
        return ["sudo pip install guildai"]

    def init_guild(self):
        return run("Init Guild", self._init_guild_cmd())

    @staticmethod
    def _init_guild_cmd():
        return ["guild init -y"]

    def uat(self):
        return run("User acceptance tests", self._uat_cmd())

    @staticmethod
    def _uat_cmd():
        return ["true"]

    def workflow_job(self):
        assert self.name
        return {
            self.name: {
                "filters": {
                    "branches": {
                        "only": "uat"
                    }
                }
            }
        }

    def _xxx_conda_notes():
        """
        # Install miniconda

        wget -P ~ http://repo.continuum.io/miniconda/Miniconda3-3.7.0-MacOSX-x86_64.sh
        bash ~/Miniconda3-3.7.0-MacOSX-x86_64.sh -b -p ~/conda

        # Init env

        ~/conda/bin/conda create --yes -p build-env-2 pip python=3.6

        # Activate env

        source ~/conda/bin/activate /Users/distiller/repo/build-env-2
        """
        pass

class MacUAT(ReleaseUAT):

    env = "macos"
    xcode_version = "9.2.0"

    def __init__(self, python):
        self.name = "uat-macos-python-%s" % python
        self.python = python

    def env_config(self):
        return {
            "xcode": self.xcode_version
        }

class Config(object):

    version = 2

    def __init__(self, workflow_jobs):
        self.workflow_jobs = workflow_jobs

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
            workflow_job.name: workflow_job.job()
            for workflow_job in self.workflow_jobs
        }

    def _workflows(self):
        return {
            "version": self.version,
            "all": {
                "jobs": [
                    workflow_job.workflow_job()
                    for workflow_job in self.workflow_jobs
                ]
            }
        }

builds = [
    LinuxBuild(python="2.7"),
    LinuxBuild(python="3.5"),
    LinuxBuild(python="3.6"),
    MacBuild(python="2.7"),
    MacBuild(python="3.6"),
    MacBuild(python="3.6"),
]

release_uats = [
    MacUAT(python="3.6")
]

def main():
    #config = Config(builds + release_uats)
    config = Config(release_uats)
    config.write()

if __name__ == "__main__":
    main()

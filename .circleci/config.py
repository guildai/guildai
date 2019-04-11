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

    cache_scheme_version = 16

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
            self._upgrade_pip(),
            self._ensure_virtual_env_cmd(),
            self._init_env(self.build_dir),
            self._activate_env(self.build_dir),
            self._install_guild_reqs(),
            self._install_tensorflow(),
            self._install_guild_view_reqs(),
        ]

    def _pip_install(self, pkgs, sudo=False):
        sudo_part = "sudo -H " if sudo else ""
        # pipe to cat effectively disables progress bar
        pkgs_part = " ".join([self._pkg_spec(pkg) for pkg in pkgs])
        return (
            "{sudo}{pip} install --upgrade {pkgs} | cat"
            .format(
                sudo=sudo_part,
                pip=self.pip,
                pkgs=pkgs_part))

    @staticmethod
    def _pkg_spec(pkg):
        if pkg.endswith(".txt"):
            return "-r {}".format(pkg)
        return pkg

    def _upgrade_pip(self):
        return self._pip_install(["pip"], sudo=True)

    def _ensure_virtual_env_cmd(self):
        return self._pip_install(["virtualenv"], sudo=True)

    @staticmethod
    def _init_env(path):
        return (
            "test -e {path}/bin/activate || virtualenv {path}"
            .format(path=path))

    @staticmethod
    def _activate_env(path):
        return ". %s/bin/activate" % path

    def _install_guild_reqs(self):
        return self._pip_install(["requirements.txt"])

    def _install_tensorflow(self):
        return self._pip_install(["grpcio==1.9.1", "tensorflow"])

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
            self._pip_install(["dist/*.whl"], sudo=True)
        ])

    def test(self):
        return self._run("Test", [
            ("guild init -y"
             " --no-progress"
             " --name guild-test"
             " --guild dist/*.whl {}".format(self.test_dir)),
            "TERM=xterm-256color source guild-env {}".format(self.test_dir),
            "WORKSPACE=%s UAT_SKIP=remote-* guild check --uat"
            % self.test_dir,
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
                        "only": ["release", "pre-release"]
                    }
                }
            }
        }

class LinuxBuild(Build):

    env = "docker"

    images = {
        "linux-python-2.7": "circleci/python:2.7-stretch-node",
        "linux-python-3.5": "circleci/python:3.5-stretch-node",
        "linux-python-3.6": "circleci/python:3.6-stretch-node",
        "linux-python-3.7": "circleci/python:3.7-stretch-node"
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

    xcode_version = "10.2.0"

    homebrew_commits = {
        "3.6": "f2a764ef944b1080be64bd88dca9a1d80130c558",
        "3.7": "22c80fc362ac8f87c59c446a85a97cb99ff160fb"
    }

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
        default_lines = super(MacBuild, self)._install_build_deps_cmd()
        mac_lines = []
        mac_lines.extend(self._python_install_cmd())
        return mac_lines + default_lines

    def _python_install_cmd(self):
        if self.python == "2.7":
            # 2.7 is default on OSX
            return []
        commit = self.homebrew_commits[self.python]
        return [
            "brew unlink python",
            ("brew install --ignore-dependencies "
             "https://raw.githubusercontent.com/Homebrew/homebrew-core/%s/"
             "Formula/python.rb > /dev/null" % self.python)
        ]

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
    LinuxBuild(python="3.7"),

    #MacBuild(python="2.7"),
    #MacBuild(python="3.6"),
    MacBuild(python="3.7"),
]

def main():
    config = Config(builds)
    config.write()

if __name__ == "__main__":
    main()

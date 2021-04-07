#!/usr/bin/env python

# Copyright 2017-2021 TensorHub, Inc.
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

    cache_scheme_version = 20

    name = None
    python = None
    env = None

    python_cmd = "python"
    pip_cmd = "python -m pip"
    pip_requires_su = True

    build_dir = "build-env"
    test_dir = "test-env"
    examples_dir = "examples"
    extra_cache_paths = []

    built_guild_cmd = "guild"
    built_guild_env_cmd = "guild-env"

    uat_skips = {}

    cache_dep_files = [
        "requirements.txt",
        "guild/view/package.json",
    ]

    upload_to_pypi = ()

    def job(self):
        assert self.env
        return {
            self.env: self.env_config(),
            "working_directory": "~/repo",
            "steps": self.steps(),
        }

    def steps(self):
        return self._base_steps() + self._maybe_upload_to_pypi()

    def _base_steps(self):
        return [
            self.checkout(),
            self.restore_cache(),
            self.install_build_deps(),
            self.save_cache(),
            self.build(),
            self.install_dist(),
            self.test(),
            self.store_artifacts(),
        ]

    def _maybe_upload_to_pypi(self):
        if self.name not in self.upload_to_pypi:
            return []
        return [
            self._run(
                "Upload to PyPI",
                [
                    self._pip_install(["twine"]),
                    "%s -m twine upload --skip-existing dist/*.whl" % self.python_cmd,
                ],
            )
        ]

    @staticmethod
    def checkout():
        return "checkout"

    def restore_cache(self):
        return {"restore_cache": {"keys": [self._cache_key()]}}

    def _cache_key(self):
        assert self.name
        checksums = "-".join(
            ["{{ checksum \"%s\" }}" % path for path in self.cache_dep_files]
        )
        return "%s-%i-%s" % (self.name, self.cache_scheme_version, checksums)

    def install_build_deps(self):
        return self._run("Install build dependencies", self._install_build_deps_cmd())

    def _install_build_deps_cmd(self):
        return [
            self._upgrade_pip(),
            self._ensure_virtual_env_cmd(),
            self._init_env(self.build_dir),
            self._activate_env(self.build_dir),
            self._install_guild_reqs(self.build_dir),
            self._install_guild_view_reqs(),
        ]

    def _pip_install(self, pkgs, venv=None):
        sudo_part = "sudo -H " if self.pip_requires_su else ""
        # pipe to cat effectively disables progress bar
        pkgs_part = " ".join([self._pkg_spec(pkg) for pkg in pkgs])
        pip_cmd = self.pip_cmd if not venv else "%s/bin/pip" % venv
        return "{sudo}{pip} install --upgrade {pkgs} | cat".format(
            sudo=sudo_part, pip=pip_cmd, pkgs=pkgs_part
        )

    @staticmethod
    def _pkg_spec(pkg):
        if pkg.endswith(".txt"):
            return "-r {}".format(pkg)
        return pkg

    def _upgrade_pip(self):
        return self._pip_install(["pip"])

    def _ensure_virtual_env_cmd(self):
        return self._pip_install(["virtualenv"])

    def _init_env(self, path):
        return "rm -rf {path} && {venv_init}".format(
            path=path, venv_init=self._venv_init_cmd(path)
        )

    def _venv_init_cmd(self, path):
        return "%s -m virtualenv %s" % (self.python_cmd, path)

    @staticmethod
    def _activate_env(path):
        return ". %s/bin/activate" % path

    def _install_guild_reqs(self, venv):
        return self._pip_install(["requirements.txt"], venv=venv)

    @staticmethod
    def _install_guild_view_reqs():
        return "cd guild/view && npm install"

    def save_cache(self):
        return {
            "save_cache": {
                "paths": [self.build_dir] + self.extra_cache_paths,
                "key": self._cache_key(),
            }
        }

    def build(self):
        return self._run(
            "Build",
            [
                ". %s/bin/activate" % self.build_dir,
                "%s/bin/python setup.py bdist_wheel" % self.build_dir,
            ],
        )

    def install_dist(self):
        return self._run("Install dist", [self._pip_install(["dist/*.whl"])])

    def test(self):
        return self._run(
            "Test",
            [
                (
                    "{built_guild} init -y"
                    " --no-progress"
                    " --name guild-test"
                    " --no-reqs"
                    " --guild dist/*.whl {test_env}".format(
                        built_guild=self.built_guild_cmd,
                        test_env=self.test_dir,
                    )
                ),
                "TERM=xterm-256color source {guild_env} {test_env}".format(
                    guild_env=self.built_guild_env_cmd,
                    test_env=self.test_dir,
                ),
                "{test_env}/bin/guild check -v --offline".format(
                    test_env=self.test_dir
                ),
                (
                    "WORKSPACE={workspace} "
                    "UAT_SKIP={uat_skip},remote-*,hiplot-* "
                    "COLUMNS=999 "
                    "EXAMPLES={examples} "
                    "GUILD_START_THRESHOLD=2.0 "
                    "DASK_SPEEDUP_THRESHOLD=1.2 "
                    "{test_env}/bin/guild check --uat".format(
                        workspace=self.test_dir,
                        examples=self.examples_dir,
                        uat_skip=",".join(self.uat_skip),
                        test_env=self.test_dir,
                    )
                ),
            ],
        )

    @staticmethod
    def store_artifacts():
        return {"store_artifacts": {"path": "dist", "destination": "dist"}}

    @staticmethod
    def _run(name, cmd_lines):
        return {
            "run": {
                "name": name,
                "command": "\n".join(cmd_lines),
                "no_output_timeout": 1800,
            }
        }

    def workflow_job(self):
        return {
            self.name: {"filters": {"branches": {"only": ["release", "pre-release"]}}}
        }


# Skip tests related to TensorFlow. Apply these skips on targets where
# the required version of TensorFlow because isn't available.
#
TENSORFLOW_UAT_SKIP = [
    "*keras*",
    "*logreg*",
    "*mnist*",
    "*tensorflow*",
    "simple-example",
    "test-flags",  # uses get-started example which requires Keras
]

PYTORCH_UAT_SKIP = [
    "*pytorch*",
]


class LinuxBuild(Build):

    env = "docker"

    images = {
        "linux-python_3.6": "circleci/python:3.6-stretch-node",
        "linux-python_3.7": "circleci/python:3.7-stretch-node",
        "linux-python_3.8": "circleci/python:3.8.1-node",
        "linux-python_3.9": "circleci/python:3.9.0-node",
    }

    uat_skips = {
        "3.8": TENSORFLOW_UAT_SKIP,
        "3.9": TENSORFLOW_UAT_SKIP + PYTORCH_UAT_SKIP,
    }

    upload_to_pypi = ("linux-python_3.6",)

    def __init__(self, python):
        self.python = python
        self.name = "linux-python_%s" % python
        self.uat_skip = self.uat_skips.get(python) or []

    def env_config(self):
        return [{"image": self.images[self.name]}]


class MacBuild(Build):

    env = "macos"

    xcode_versions = {
        "10.14": "11.1.0",
        "10.15": "11.2.1",
    }

    pyenv_versions = {
        "3.6": "3.6.11",
        "3.7": "3.7.9",
        "3.8": "3.8.6",
        "3.9": "3.9.0",
    }

    python_cmds = {
        "3.6": "~/.pyenv/versions/3.6.11/bin/python",
        "3.7": "~/.pyenv/versions/3.7.9/bin/python",
        "3.8": "~/.pyenv/versions/3.8.6/bin/python",
        "3.9": "~/.pyenv/versions/3.9.0/bin/python",
    }

    pip_cmds = {
        # ver: (cmd, pip_requires_su)
        "3.6": ("~/.pyenv/versions/3.6.11/bin/python -m pip", False),
        "3.7": ("~/.pyenv/versions/3.7.9/bin/python -m pip", False),
        "3.8": ("~/.pyenv/versions/3.8.6/bin/python -m pip", False),
        "3.9": ("~/.pyenv/versions/3.9.0/bin/python -m pip", False),
    }

    guild_cmds = {
        "3.6": "~/.pyenv/versions/3.6.11/bin/guild",
        "3.7": "~/.pyenv/versions/3.7.9/bin/guild",
        "3.8": "~/.pyenv/versions/3.8.6/bin/guild",
        "3.9": "~/.pyenv/versions/3.9.0/bin/guild",
    }

    guild_env_cmds = {
        "3.6": "~/.pyenv/versions/3.6.11/bin/guild-env",
        "3.7": "~/.pyenv/versions/3.7.9/bin/guild-env",
        "3.8": "~/.pyenv/versions/3.8.6/bin/guild-env",
        "3.9": "~/.pyenv/versions/3.9.0/bin/guild-env",
    }

    extra_cache_paths = [
        "/usr/local/Homebrew",
    ]

    uat_skips = {
        "3.8": TENSORFLOW_UAT_SKIP,
        "3.9": TENSORFLOW_UAT_SKIP + PYTORCH_UAT_SKIP,
    }

    def __init__(self, os_version, python):
        self.xcode_version = self.xcode_versions[os_version]
        self.python = python
        self.name = "macos_%s-python_%s" % (os_version, python)
        self.python_cmd = self.python_cmds.get(self.python, self.python_cmd)
        (self.pip_cmd, self.pip_requires_su) = self.pip_cmds.get(
            self.python, (self.pip_cmd, self.pip_requires_su)
        )
        self.built_guild_cmd = self.guild_cmds[self.python]
        self.built_guild_env_cmd = self.guild_env_cmds.get(
            self.python, self.built_guild_env_cmd
        )
        self.uat_skip = self.uat_skips.get(python) or []

    def env_config(self):
        return {"xcode": self.xcode_version}

    def _install_build_deps_cmd(self):
        default_lines = super(MacBuild, self)._install_build_deps_cmd()
        mac_lines = []
        mac_lines.extend(self._python_install_cmd())
        return mac_lines + default_lines

    def _python_install_cmd(self):
        pyenv_ver = self.pyenv_versions[self.python]
        return [
            "brew install pyenv",
            "pyenv install %s" % pyenv_ver,
        ]


class Config(object):

    version = 2

    def __init__(self, builds):
        self.builds = builds

    def write(self):
        config = {
            "version": self.version,
            "jobs": self._jobs(),
            "workflows": self._workflows(),
        }
        with open("config.yml", "w") as out:
            yaml.dump(config, out, default_flow_style=False, width=9999)

    def _jobs(self):
        return {build.name: build.job() for build in self.builds}

    def _workflows(self):
        return {
            "version": self.version,
            "all": {"jobs": [build.workflow_job() for build in self.builds]},
        }


builds = [
    LinuxBuild(python="3.6"),
    LinuxBuild(python="3.7"),
    LinuxBuild(python="3.8"),
    LinuxBuild(python="3.9"),
    MacBuild("10.15", python="3.6"),
    MacBuild("10.15", python="3.7"),
    MacBuild("10.15", python="3.8"),
    MacBuild("10.15", python="3.9"),
]


def main():
    config = Config(builds)
    config.write()


if __name__ == "__main__":
    main()

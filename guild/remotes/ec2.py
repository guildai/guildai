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

from __future__ import absolute_import
from __future__ import division

import json
import logging
import os
import re
import subprocess
import sys

import guild.remote

from guild import util
from guild import var

from . import ssh_util

log = logging.getLogger("guild.remotes.ec2")

class EC2Remote(guild.remote.Remote):

    def __init__(self, name, config):
        self.name = name
        self.region = config["region"]
        self.ami = config["ami"]
        self.public_key = config["public-key"]
        self.instance_type = config.get("instance_type", "p3.2xlarge")
        self.public_key = config.get("public-key")
        self.private_key_path = config.get("private-key-path")
        self.user = config.get("user")
        self.init = config.get("init")
        self.working_dir = var.remote_dir(name)

    def start(self):
        self._verify_aws_creds()
        util.ensure_dir(self.working_dir)
        self._refresh_config()
        self._ensure_terraform_init()
        self._terraform_apply()

    def reinit(self):
        self._taint_init()
        self.start()

    def _taint_init(self):
        cmd = [
            "terraform",
            "taint",
            "null_resource.guild_%s_init" % self._safe_name()
        ]
        subprocess.check_call(cmd, cwd=self.working_dir)

    def _safe_name(self):
        return re.sub(r"\W|^(?=\d)", "_", self.name)

    def _verify_aws_creds(self):
        self._require_env("AWS_ACCESS_KEY_ID")
        self._require_env("AWS_SECRET_ACCESS_KEY")

    def stop(self):
        self._verify_aws_creds()
        self._terraform_destroy()

    def status(self, verbose=False):
        if not self._has_state():
            raise guild.remote.Down("not started")
        if self._empty_state():
            raise guild.remote.Down("not running")
        host = self._output("host")[0]
        ssh_util.ssh_ping(host, verbose)
        sys.stdout.write("%s (%s) is available\n" % (self.name, host))

    def _has_state(self):
        state_filename = os.path.join(self.working_dir, "terraform.tfstate")
        return os.path.exists(state_filename)

    def _empty_state(self):
        cmd = ["terraform", "show", "-no-color"]
        try:
            out = subprocess.check_output(cmd, cwd=self.working_dir)
        except subprocess.CalledProcessError:
            return False
        else:
            return not out.strip()

    def _output(self, name):
        cmd = ["terraform", "output", "-json"]
        try:
            out = subprocess.check_output(cmd, cwd=self.working_dir)
        except subprocess.CalledProcessError:
            raise guild.remote.OperationError(
                "unable to get Terraform output in %s"
                % self.working_dir)
        else:
            output = json.loads(out.decode())
            return output[name]["value"]

    def _refresh_config(self):
        config_filename = os.path.join(self.working_dir, "config.tf.json")
        config = self._init_config()
        with open(config_filename, "w") as out:
            json.dump(config, out)

    def _init_config(self):
        safe_name = self._safe_name()
        config = {
            "provider": {
                "aws": {
                    "region": self.region
                }
            },
            "resource": {
                "aws_default_vpc": {
                    "guild_%s" % safe_name: {}
                },
                "aws_security_group": {
                    "guild_%s" % safe_name: {
                        "name": "guild-%s" % safe_name,
                        "description": ("Security group for Guild remote %s"
                                        % safe_name),
                        "vpc_id": "${aws_default_vpc.guild_%s.id}" % safe_name,
                        "ingress": [
                            {
                                "from_port": -1,
                                "to_port": -1,
                                "protocol": "icmp",
                                "cidr_blocks": ["0.0.0.0/0"]
                            },
                            {
                                "from_port": 22,
                                "to_port": 22,
                                "protocol": "tcp",
                                "cidr_blocks": ["0.0.0.0/0"]
                            }
                        ],
                        "egress": [
                            {
                                "from_port": 0,
                                "to_port": 0,
                                "protocol": "-1",
                                "cidr_blocks": ["0.0.0.0/0"]
                            }
                        ]
                    }
                },
                "aws_key_pair": {
                    "guild_%s" % safe_name: {
                        "key_name": "guild_%s" % safe_name,
                        "public_key": self.public_key
                    }
                },
                "aws_instance": {
                    "guild_%s" % safe_name: {
                        "instance_type": self.instance_type,
                        "ami": self.ami,
                        "count": 1,
                        "vpc_security_group_ids": [
                            "${aws_security_group.guild_%s.id}" % safe_name
                        ],
                        "key_name": "guild_%s" % safe_name
                    }
                }
            },
            "output": {
                "host": {
                    "value": "${aws_instance.guild_%s.*.public_dns}" % safe_name
                }
            }
        }
        if self.init:
            self._write_init_script()
            connection = {
                "host": "${aws_instance.guild_%s.public_ip}" % safe_name
            }
            if self.user:
                connection["user"] = self.user
            if self.private_key_path:
                connection["private_key"] = (
                    "${file(\"%s\")}" % self.private_key_path
                )
            config["resource"]["null_resource"] = {
                "guild_%s_init" % safe_name: {
                    "triggers": {
                        "cluster_instance_ids":
                        "${aws_instance.guild_%s.id}" % safe_name
                    },
                    "connection": connection,
                    "provisioner": [
                        {
                            "remote-exec": {
                                "script": "init.sh"
                            }
                        }
                    ]
                }
            }
        return config

    def _write_init_script(self):
        assert self.init
        init_filename = os.path.join(self.working_dir, "init.sh")
        with open(init_filename, "w") as f:
            f.write(self.init)
        return init_filename

    @staticmethod
    def _apply_remote_exec_provisioner(config, init_filename):
        config["provisioner"] = {
            "remote-exec": {
                "scripts": [init_filename]
            }
        }

    def _ensure_terraform_init(self):
        if os.path.exists(os.path.join(self.working_dir, ".terraform")):
            return
        cmd = ["terraform", "init"]
        result = subprocess.call(cmd, cwd=self.working_dir)
        if result != 0:
            raise guild.remote.OperationError(
                "unable to initialize Terraform in %s"
                % self.working_dir)

    def _terraform_apply(self):
        cmd = ["terraform", "apply", "-auto-approve"]
        result = subprocess.call(cmd, cwd=self.working_dir)
        if result != 0:
            raise guild.remote.OperationError(
                "error applying Terraform config in %s"
                % self.working_dir)

    @staticmethod
    def _require_env(name):
        if name not in os.environ:
            raise guild.remote.OperationError(
                "missing required %s environment variable"
                % name)

    def _terraform_destroy(self):
        cmd = ["terraform", "destroy", "-auto-approve"]
        result = subprocess.call(cmd, cwd=self.working_dir)
        if result != 0:
            raise guild.remote.OperationError(
                "error destroying Terraform state in %s"
                % self.working_dir)

    def push(self, runs, verbose=False):
        raise NotImplementedError()

    def push_dest(self):
        raise NotImplementedError()

    def pull(self, run_ids, verbose=False):
        raise NotImplementedError()

    def pull_all(self, verbose=False):
        raise NotImplementedError()

    def pull_src(self):
        raise NotImplementedError()

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

from guild import remote as remotelib
from guild import remote_util
from guild import util
from guild import var

from . import ssh as ssh_remote
from . import ssh_util

log = logging.getLogger("guild.remotes.ec2")

class EC2Remote(remotelib.Remote):

    def __init__(self, name, config):
        self.name = name
        self.region = config["region"]
        self.ami = config["ami"]
        self.instance_type = config["instance-type"]
        self.public_key = config.get("public-key")
        self.connection = config.get("connection", {})
        self.init = config.get("init")
        self.working_dir = var.remote_dir(name)

    def start(self):
        self._verify_aws_creds()
        self._verify_terraform()
        util.ensure_dir(self.working_dir)
        self._refresh_config()
        self._ensure_terraform_init()
        self._terraform_apply()

    def reinit(self):
        self._verify_terraform()
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

    @staticmethod
    def _verify_aws_creds():
        remote_util.require_env("AWS_ACCESS_KEY_ID")
        remote_util.require_env("AWS_SECRET_ACCESS_KEY")

    @staticmethod
    def _verify_terraform():
        if not util.which("terraform"):
            raise remotelib.OperationError(
                "Terraform is required for this operation - refer to "
                "https://www.terraform.io/intro/getting-started/install.html "
                "for more information.")

    def stop(self):
        self._verify_aws_creds()
        self._verify_terraform()
        self._terraform_destroy()

    def status(self, verbose=False):
        self._verify_aws_creds()
        self._verify_terraform()
        if os.path.exists(self.working_dir):
            self._refresh_config()
        if not self._has_state():
            raise remotelib.Down("not started")
        if verbose:
            self._terraform_show()
        else:
            self._try_ping_host(verbose)

    def _terraform_refresh(self):
        log.info("Getting remote status")
        cmd = ["terraform", "refresh", "-no-color"]
        subprocess.check_output(cmd, cwd=self.working_dir)

    def _terraform_show(self):
        self._terraform_refresh()
        cmd = ["terraform", "show", "-no-color"]
        subprocess.call(cmd, cwd=self.working_dir)

    def _try_ping_host(self, verbose):
        if self._empty_state():
            raise remotelib.Down("not started")
        self._terraform_refresh()
        try:
            host = self._output("host")
        except LookupError:
            raise remotelib.Down("not running")
        else:
            if not host:
                raise remotelib.Down("stopped")
            user = self.connection.get("user")
            ssh_util.ssh_ping(host, user, verbose)
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
            raise remotelib.OperationError(
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
        remote_name = self._safe_name()
        remote_key = "guild_%s" % remote_name
        vpc = {
            remote_key: {}
        }
        security_group = {
            remote_key: {
                "name": "guild-%s" % remote_name,
                "description": ("Security group for Guild remote %s"
                                % remote_name),
                "vpc_id": "${aws_default_vpc.%s.id}" % remote_key,
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
        }
        instance = {
            remote_key: {
                "instance_type": self.instance_type,
                "ami": self.ami,
                "count": 1,
                "vpc_security_group_ids": [
                    "${aws_security_group.%s.id}" % remote_key
                ]
            }
        }
        output = {
            "host": {
                "value": "${aws_instance.%s.public_dns}" % remote_key
            }
        }
        config = {
            "provider": {
                "aws": {
                    "region": self.region
                },
                "null": {}
            },
            "resource": {
                "aws_default_vpc": vpc,
                "aws_security_group": security_group,
                "aws_instance": instance
            },
            "output": output
        }
        public_key = self._public_key()
        if public_key:
            config["resource"]["aws_key_pair"] = {
                remote_key: {
                    "key_name": remote_key,
                    "public_key": public_key
                }
            }
            instance[remote_key]["key_name"] = remote_key
        init_script = self._init_script()
        if init_script:
            init_script_path = self._write_init_script(init_script)
            connection = {
                "type": "ssh",
                "host": "${aws_instance.%s.public_ip}" % remote_key
            }
            if "timeout" in self.connection:
                connect_timeout = self.connection["timeout"]
                if isinstance(connect_timeout, int):
                    connect_timeout = "%im" % connect_timeout
                connection["timeout"] = connect_timeout
            if "private-key" in self.connection:
                connection["private_key"] = (
                    "${file(\"%s\")}" % self.connection["private-key"]
                )
            connection.update({
                name: self.connection[name]
                for name in ["user", "password", "port"]
                if name in self.connection
            })
            config["resource"]["null_resource"] = {
                "%s_init" % remote_key: {
                    "triggers": {
                        "cluster_instance_ids":
                        "${aws_instance.%s.id}" % remote_key
                    },
                    "connection": connection,
                    "provisioner": [
                        {
                            "remote-exec": {
                                "script": init_script_path
                            }
                        }
                    ]
                }
            }
        return config

    def _public_key(self):
        if not self.public_key:
            return None
        maybe_path = os.path.expanduser(os.path.expandvars(self.public_key))
        if os.path.exists(maybe_path):
            return open(maybe_path, "r").read()
        else:
            return self.public_key

    def _init_script(self):
        return self.init or ""

    def _write_init_script(self, init_script):
        init_filename = os.path.join(self.working_dir, "init.sh")
        with open(init_filename, "w") as f:
            f.write(init_script)
        return init_filename

    def _ensure_terraform_init(self):
        if os.path.exists(os.path.join(self.working_dir, ".terraform")):
            return
        cmd = ["terraform", "init"]
        result = subprocess.call(cmd, cwd=self.working_dir)
        if result != 0:
            raise remotelib.OperationError(
                "unable to initialize Terraform in %s"
                % self.working_dir)

    def _terraform_apply(self):
        cmd = ["terraform", "apply", "-auto-approve"]
        result = subprocess.call(cmd, cwd=self.working_dir)
        if result != 0:
            raise remotelib.OperationError(
                "error applying Terraform config in %s"
                % self.working_dir)

    def _terraform_destroy(self):
        cmd = ["terraform", "destroy", "-auto-approve"]
        result = subprocess.call(cmd, cwd=self.working_dir)
        if result != 0:
            raise remotelib.OperationError(
                "error destroying Terraform state in %s"
                % self.working_dir)

    def push(self, runs, no_delete=False):
        raise NotImplementedError()

    def pull(self, runs, no_delete=False):
        raise NotImplementedError()

    def list_runs(self, verbose=False, **filters):
        ssh_remote = self._ssh_remote()
        ssh_remote.list_runs(verbose, **filters)

    def _ssh_remote(self):
        config = dict(
            host=self._ssh_host(),
            user=self.connection.get("user")
        )
        return ssh_remote.SSHRemote(self.name, config)

    def _ssh_host(self):
        try:
            host = self._output("host")
        except LookupError:
            raise remotelib.OperationError(
                "cannot get host for %s - is the remote started?"
                % self.name)
        else:
            if not host:
                raise remotelib.OperationError(
                    "cannot get host for %s - the instance "
                    "appears to be stopped"
                    % self.name)
            return host

    def run_op(self, opspec, args, restart, no_wait, **opts):
        ssh_remote = self._ssh_remote()
        return ssh_remote.run_op(opspec, args, restart, no_wait, **opts)

    def one_run(self, run_id_prefix, attrs):
        ssh_remote = self._ssh_remote()
        return ssh_remote.one_run(run_id_prefix, attrs)

    def watch_run(self, **opts):
        ssh_remote = self._ssh_remote()
        ssh_remote.watch_run(**opts)

    def delete_runs(self, **opts):
        ssh_remote = self._ssh_remote()
        ssh_remote.delete_runs(**opts)

    def restore_runs(self, **opts):
        ssh_remote = self._ssh_remote()
        ssh_remote.restore_runs(**opts)

    def purge_runs(self, **opts):
        ssh_remote = self._ssh_remote()
        ssh_remote.purge_runs(**opts)

    def label_runs(self, **opts):
        ssh_remote = self._ssh_remote()
        ssh_remote.label_runs(**opts)

    def run_info(self, **opts):
        ssh_remote = self._ssh_remote()
        ssh_remote.run_info(**opts)

    def check(self, **opts):
        ssh_remote = self._ssh_remote()
        ssh_remote.check(**opts)

    def stop_runs(self, **opts):
        ssh_remote = self._ssh_remote()
        ssh_remote.stop_runs(**opts)

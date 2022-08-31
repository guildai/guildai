# Copyright 2017-2022 RStudio, PBC
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


class EC2RemoteType(remotelib.RemoteType):
    def __init__(self, _ep):
        pass

    def remote_for_config(self, name, config):
        return EC2Remote(name, config)

    def remote_for_spec(self, spec):
        raise NotImplementedError()


class EC2Remote(ssh_remote.SSHRemote):
    def __init__(self, name, config):
        self.name = name
        self.region = config["region"]
        self.ami = config["ami"]
        self.instance_type = config["instance-type"]
        self.root_device_size = config.get("root-device-size")
        self.public_key = config.get("public-key")
        self.private_key = config.get("private-key")
        self.working_dir = var.remote_dir(name)
        self.init_timeout = config.get("init-timeout")
        super().__init__(name, self._ensure_none_host(config))

    def _ensure_none_host(self, config):
        if "host" in config:
            log.warning("config 'host' ignored in remote %s", self.name)
        config = dict(config)
        config["host"] = None
        return config

    @property
    def host(self):
        return self._ssh_host()

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
        cmd = ["terraform", "taint", f"null_resource.guild_{self._safe_name()}_init"]
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
                "for more information."
            )

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
        except LookupError as e:
            raise remotelib.Down("not running") from e
        else:
            if not host:
                raise remotelib.Down("stopped")
            ssh_util.ssh_ping(
                host,
                user=self.user,
                private_key=self.private_key,
                verbose=verbose,
                connect_timeout=self.connect_timeout,
                port=self.port,
            )
            sys.stdout.write(f"{self.name} ({host}) is available\n")

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
        except subprocess.CalledProcessError as e:
            raise remotelib.OperationError(
                f"unable to get Terraform output in {self.working_dir}"
            ) from e
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
        remote_key = f"guild_{remote_name}"
        vpc = {remote_key: {}}
        security_group = {
            remote_key: {
                "name": f"guild-${remote_name}",
                "description": f"Security group for Guild remote {remote_name}",
                "vpc_id": f"${{aws_default_vpc.{remote_key}.id}}",
                "ingress": [
                    {
                        "from_port": -1,
                        "to_port": -1,
                        "protocol": "icmp",
                        "cidr_blocks": ["0.0.0.0/0"],
                        "description": None,
                        "ipv6_cidr_blocks": None,
                        "prefix_list_ids": None,
                        "security_groups": None,
                        "self": None,
                    },
                    {
                        "from_port": 22,
                        "to_port": 22,
                        "protocol": "tcp",
                        "cidr_blocks": ["0.0.0.0/0"],
                        "description": None,
                        "ipv6_cidr_blocks": None,
                        "prefix_list_ids": None,
                        "security_groups": None,
                        "self": None,
                    },
                ],
                "egress": [
                    {
                        "from_port": 0,
                        "to_port": 0,
                        "protocol": "-1",
                        "cidr_blocks": ["0.0.0.0/0"],
                        "description": None,
                        "ipv6_cidr_blocks": None,
                        "prefix_list_ids": None,
                        "security_groups": None,
                        "self": None,
                    }
                ],
            }
        }
        instance = {
            remote_key: {
                "instance_type": self.instance_type,
                "ami": self.ami,
                "vpc_security_group_ids": [f"${{aws_security_group.{remote_key}.id}}"],
            }
        }
        if self.root_device_size:
            instance[remote_key]["root_block_device"] = {
                "volume_size": self.root_device_size
            }
        output = {"host": {"value": "${{aws_instance.{remote_key}.public_dns}}"}}
        config = {
            "provider": {"aws": {"region": self.region}, "null": {}},
            "resource": {
                "aws_default_vpc": vpc,
                "aws_security_group": security_group,
                "aws_instance": instance,
            },
            "output": output,
        }
        public_key = self._public_key()
        if public_key:
            config["resource"]["aws_key_pair"] = {
                remote_key: {"key_name": remote_key, "public_key": public_key}
            }
            instance[remote_key]["key_name"] = remote_key
        init_script = self._init_script()
        if init_script:
            init_script_path = self._write_init_script(init_script)
            connection = {
                "type": "ssh",
                "host": f"${{aws_instance.{remote_key}.public_ip}}",
            }
            if self.init_timeout:
                if isinstance(self.init_timeout, int):
                    connection["timeout"] = f"{self.init_timeout}m"
                else:
                    connection["timeout"] = self.init_timeout
            if self.private_key:
                private_key_path = remote_util.config_path(self.private_key)
                connection["private_key"] = f"${{file(\"{private_key_path}\")}}"
            if self.user:
                connection["user"] = self.user
            config["resource"]["null_resource"] = {
                f"{remote_key}_init": {
                    "triggers": {
                        "cluster_instance_ids": f"${{aws_instance.{remote_key}.id}}"
                    },
                    "connection": connection,
                    "provisioner": [{"remote-exec": {"script": init_script_path}}],
                }
            }
        return config

    def _public_key(self):
        if not self.public_key:
            return None
        maybe_path = remote_util.config_path(self.public_key)
        if os.path.exists(maybe_path):
            return open(maybe_path, "r").read()
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
                f"unable to initialize Terraform in {self.working_dir}"
            )

    def _terraform_apply(self):
        cmd = ["terraform", "apply", "-auto-approve"]
        result = subprocess.call(cmd, cwd=self.working_dir)
        if result != 0:
            raise remotelib.OperationError(
                f"error applying Terraform config in {self.working_dir}"
            )

    def _terraform_destroy(self):
        cmd = ["terraform", "destroy", "-auto-approve"]
        result = subprocess.call(cmd, cwd=self.working_dir)
        if result != 0:
            raise remotelib.OperationError(
                f"error destroying Terraform state in {self.working_dir}"
            )

    def _ssh_host(self):
        try:
            host = self._output("host")
        except LookupError as e:
            raise remotelib.OperationError(
                f"cannot get host for {self.name} - is the remote started?"
            ) from e
        else:
            if not host:
                raise remotelib.OperationError(
                    f"cannot get host for {self.name} - the instance "
                    "appears to be stopped"
                )
            return host

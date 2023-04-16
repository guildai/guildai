# Copyright 2017-2023 Posit Software, PBC
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

log = logging.getLogger("guild.remotes.azure_vm")


class AzureVMRemoteType(remotelib.RemoteType):
    def __init__(self, _ep):
        pass

    def remote_for_config(self, name, config):
        return AzureVMRemote(name, config)

    def remote_for_spec(self, spec):
        raise NotImplementedError()


class AzureVMRemote(ssh_remote.SSHRemote):
    def __init__(self, name, config):
        self.name = name
        self.region = config["region"]
        self.image = config["image"]
        self.instance_type = config["instance-type"]
        self.root_device_size = config.get("root-device-size")
        self.disk_type = config.get("disk-type")
        self.public_key = config["public-key"]
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
        self._verify_azure_creds()
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
        return re.sub(r"\W|^(?=\d)", "-", self.name)

    @staticmethod
    def _verify_azure_creds():
        if util.which("az"):
            cmd_login = ["az", "account", "list-locations"]
            devnull = open(os.devnull, "w")
            try:
                out = subprocess.check_output(cmd_login, stderr=devnull)
            except subprocess.CalledProcessError as e:
                raise remotelib.OperationError(
                    "User must be logged into Azure CLI - run 'az login' or refer to "
                    "https://docs.microsoft.com/en-us/cli/azure/authenticate-azure-cli "
                    "for more information."
                ) from e
            else:
                return out.decode("utf-8").split(os.linesep, 1)[0]
        else:
            raise remotelib.OperationError(
                "Azure CLI is required for this operation - refer to "
                "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli "
                "for more information."
            )

    @staticmethod
    def _verify_terraform():
        if not util.which("terraform"):
            raise remotelib.OperationError(
                "Terraform is required for this operation - refer to "
                "https://www.terraform.io/intro/getting-started/install.html "
                "for more information."
            )

    def stop(self):
        self._verify_azure_creds()
        self._verify_terraform()
        self._terraform_destroy()

    def status(self, verbose=False):
        self._verify_azure_creds()
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
        resource_group = {
            remote_key: {
                "name": f"guild-{remote_name}-rg",
                "location": self.region
            }
        }
        vnet = {
            remote_key: {
                "name": f"guild-{remote_name}-vnet",
                "address_space": ["10.0.0.0/16"],
                "location": self.region,
                "resource_group_name": f"${{azurerm_resource_group.{remote_key}.name}}",
            }
        }
        subnet = {
            remote_key: {
                "name": f"guild-{remote_name}-subnet",
                "resource_group_name": f"${{azurerm_resource_group.{remote_key}.name}}",
                "virtual_network_name": (
                    f"${{azurerm_virtual_network.{remote_key}.name}}"
                ),
                "address_prefixes": ["10.0.1.0/24"],
            }
        }
        public_ip = {
            remote_key: {
                "name": f"guild-{remote_name}-public-ip",
                "location": self.region,
                "resource_group_name": f"${{azurerm_resource_group.{remote_key}.name}}",
                "allocation_method": "Static",
            }
        }
        nsg = {
            remote_key: {
                "name": f"guild-{remote_name}-nsg",
                "location": self.region,
                "resource_group_name": f"${{azurerm_resource_group.{remote_key}.name}}",
            }
        }
        nsr = {
            remote_key: {
                "name": "SSH",
                "priority": "1001",
                "direction": "Inbound",
                "access": "Allow",
                "protocol": "Tcp",
                "source_port_range": "*",
                "destination_port_range": "22",
                "source_address_prefix": "*",
                "destination_address_prefix": "*",
                "resource_group_name": f"${{azurerm_resource_group.{remote_key}.name}}",
                "network_security_group_name": (
                    f"${{azurerm_network_security_group.{remote_key}.name}}"
                ),
            }
        }
        nic = {
            remote_key: {
                "name": f"guild-{remote_name}-nic",
                "location": self.region,
                "resource_group_name": f"${{azurerm_resource_group.{remote_key}.name}}",
                "ip_configuration": {
                    "name": f"guild-{remote_name}-nicconf",
                    "subnet_id": f"${{azurerm_subnet.{remote_key}.id}}",
                    "private_ip_address_allocation": "dynamic",
                    "public_ip_address_id": f"${{azurerm_public_ip.{remote_key}.id}}",
                },
            }
        }
        if "id" in self.image:
            image_reference = {"id": self.image["id"]}
        elif "urn" in self.image:
            urn = self.image["urn"].split(':')
            image_reference = {
                "publisher": urn[0],
                "offer": urn[1],
                "sku": urn[2],
                "version": urn[3],
            }
        else:
            image_reference = {
                "publisher": self.image["publisher"],
                "offer": self.image["offer"],
                "sku": self.image["sku"],
            }
            if self.image["version"]:
                image_reference["version"] = self.image["version"]
        if self.disk_type:
            disk_type = self.disk_type
        else:
            disk_type = "Premium_LRS"
        instance = {
            remote_key: {
                "name": f"guild-{remote_name}-vm",
                "location": self.region,
                "resource_group_name": f"${{azurerm_resource_group.{remote_key}.name}}",
                "network_interface_ids": [
                    f"${{azurerm_network_interface.{remote_key}.id}}"
                ],
                "vm_size": self.instance_type,
                "storage_os_disk": {
                    "name": f"guild-{remote_name}-osdisk",
                    "caching": "ReadWrite",
                    "create_option": "FromImage",
                    "managed_disk_type": disk_type,
                },
                "storage_image_reference": image_reference,
                "os_profile": {
                    "computer_name": f"guild-{remote_name}-vm",
                    "admin_username": "",
                },
                "os_profile_linux_config": {
                    "disable_password_authentication": "true",
                    "ssh_keys": {},
                },
            }
        }
        if self.root_device_size:
            instance[remote_key]["storage_os_disk"]["disk_size_gb"] = (
                self.root_device_size
            )
        output = {"host": {"value": f"${{azurerm_public_ip.{remote_key}.ip_address}}"}}
        config = {
            "provider": {
                "azurerm": {
                    "features": {}
                },
                "null": {}
            },
            "resource": {
                "azurerm_resource_group": resource_group,
                "azurerm_virtual_network": vnet,
                "azurerm_subnet": subnet,
                "azurerm_public_ip": public_ip,
                "azurerm_network_security_group": nsg,
                "azurerm_network_security_rule": nsr,
                "azurerm_network_interface": nic,
                "azurerm_virtual_machine": instance,
            },
            "output": output,
        }
        if not self.user:
            self.user = util.user()
            config["resource"]["azurerm_virtual_machine"][remote_key]["os_profile"][
                "admin_username"] = self.user
        public_key = self._public_key()
        config["resource"]["azurerm_virtual_machine"][remote_key][
            "os_profile_linux_config"]["ssh_keys"]["key_data"] = public_key
        config["resource"]["azurerm_virtual_machine"][remote_key][
            "os_profile_linux_config"]["ssh_keys"][
                "path"] = f"/home/{self.user}/.ssh/authorized_keys"
        init_script = self._init_script()
        if init_script:
            init_script_path = self._write_init_script(init_script)
            connection = {
                "type": "ssh",
                "host": f"${{azurerm_public_ip.{remote_key}.ip_address}}",
            }
            if self.init_timeout:
                if isinstance(self.init_timeout, int):
                    connection["timeout"] = f"{self.init_timeout}m"
                else:
                    connection["timeout"] = self.init_timeout
            if self.private_key:
                private_key_path = remote_util.config_path(self.private_key)
                connection["private_key"] = f"${{file(\"{private_key_path}\")}}"
            connection["user"] = self.user
            config["resource"]["null_resource"] = {
                f"{remote_key}_init": {
                    "triggers": {
                        "cluster_instance_ids": (
                            f"${{azurerm_virtual_machine.{remote_key}.id}}"
                        )
                    },
                    "connection": connection,
                    "provisioner": [{
                        "remote-exec": {
                            "script": init_script_path
                        }
                    }],
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

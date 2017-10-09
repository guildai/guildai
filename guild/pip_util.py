import logging
import os

from pip._internal.commands.install import InstallCommand
from pip._internal.wheel import Wheel

import guild.var

def install(reqs, upgrade=False):
    cmd = InstallCommand()
    args = ["-t", guild.var.dist_packages_dir()]
    if upgrade:
        args.append("--upgrade")
    args.extend(reqs)
    cmd.run(*cmd.parse_args(args))

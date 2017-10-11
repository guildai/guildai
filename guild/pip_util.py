import logging
import os

from pip._internal.commands.install import InstallCommand
from pip._internal.wheel import Wheel

def install(reqs, upgrade=False):
    cmd = InstallCommand()
    args = ["--user"]
    if upgrade:
        args.append("--upgrade")
    args.extend(reqs)
    cmd.run(*cmd.parse_args(args))

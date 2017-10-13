import logging
import os

from pip.commands.install import InstallCommand
from pip.utils import get_installed_distributions
from pip.wheel import Wheel

class Distribution(object):

    def __init__(self, d):
        self._d = d

    def __str__(self):
        return str(self._d)

    @property
    def name(self):
        return self._d.project_name

    @property
    def version(self):
        return self._d.version

def install(reqs, index_urls=None, upgrade=False):
    cmd = InstallCommand()
    args = ["--user"]
    if upgrade:
        args.append("--upgrade")
    if index_urls:
        args.append("--index-url", index_urls[0])
        for url in index_urls[1:]:
            args.append("--extra-index-url", url)
    args.extend(reqs)
    cmd.run(*cmd.parse_args(args))

def get_installed():
    installed = get_installed_distributions(user_only=True)
    return [Distribution(d) for d in installed]

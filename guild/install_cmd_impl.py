import pip

import guild.package
import guild.pip_util

def main(args):
    python_reqs = [
        guild.package.guild_to_python(req)
        for req in args.packages
    ]
    guild.pip_util.install(python_reqs, args.upgrade)

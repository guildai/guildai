import pip

import guild.pip_util

def main(args):
    guild.pip_util.install(args.packages, args.upgrade)

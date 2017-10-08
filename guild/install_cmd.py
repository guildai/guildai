import pip

import guild.package

def main(args):
    for pkg in args.packages:
        guild.package.install(pkg)

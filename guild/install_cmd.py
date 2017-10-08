import pip

import guild.install

def main(args):
    for pkg in args.packages:
        guild.install.install_package(pkg, args.force)

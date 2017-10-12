import guild.cli
import guild.package
import guild.pip_util

def list_packages(_args):
    pkgs = [_format_pkg(pkg) for pkg in guild.pip_util.get_installed()]
    guild.cli.table(pkgs, cols=["name", "version"], sort=["name"])

def _format_pkg(pkg):
    return {
        "name": guild.package.apply_namespace(pkg.name),
        "version": pkg.version,
    }

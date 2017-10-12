import guild.cli
import guild.cmd_support
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

def install_packages(args):
    for reqs, index_urls in _install_cmds(args):
        print("*****", reqs, index_urls)
        #guild.pip_util.install(reqs, index_urls, args.upgrade)

def _install_cmds(args):
    index_urls = {}
    for pkg in args.packages:
        ns, req_in = guild.cmd_support.split_pkg(pkg)
        req, urls = ns.pip_install_info(req_in)
        urls_key = "\n".join(urls)
        index_urls.setdefault(urls_key, []).append(req)
    return [
        (reqs, urls_key.split("\n"))
        for urls_key, reqs in index_urls.items()
    ]

def delete_packages(args):
    print("TODO: delete %s" % args.packages)

def uninstall_packages(args):
    print("TODO: uninstall %s" % (args.packages,))

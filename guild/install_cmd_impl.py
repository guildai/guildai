import guild.cmd_support
import guild.pip_util

def main(args):
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

import guild.var

def list_packages(_args):
    packages = _format_packages(guild.var.packages())
    guild.cli.table(packages, cols=["name", "versions"])

def _format_packages(pkgs):
    """Consolidates a list of pkg/ver into a list of unique pkg w/versions.

    For example:

      foo 1
      foo 2
      bar 2

    becomes:

      foo 1,2
      bar 2

    """
    if not pkgs:
        return []
    formatted = []
    pkgs = sorted(pkgs)
    cur_name = None
    vers = []
    def acc():
        formatted.append({
            "name": cur_name,
            "versions": ", ".join(vers)
        })
    for pkg in pkgs:
        if cur_name is None:
            cur_name = pkg.name
        if pkg.name == cur_name:
            vers.append(pkg.version)
        else:
            acc()
            cur_name = pkg.name
            vers = [pkg.version]
    acc()
    return formatted

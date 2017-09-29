#-*-python-*-

def guild_python_workspace():

    native.new_http_archive(
        name = "org_click",
        build_file = "//third-party:click.BUILD",
        urls = [
            "https://github.com/pallets/click/archive/752ff79d680fceb26d2a93f1eef376d90823ec47.zip",
        ],
        strip_prefix = "click-752ff79d680fceb26d2a93f1eef376d90823ec47",
        sha256 = "ecbdbd641b388b072b3b21d94622d7288df61a1e9643b978081d0ee173791c70",
    )

    native.new_http_archive(
        name = "org_pyyaml",
        build_file = "//third-party:pyyaml.BUILD",
        urls = [
            "https://pypi.python.org/packages/4a/85/db5a2df477072b2902b0eb892feb37d88ac635d36245a72a6a69b23b383a/PyYAML-3.12.tar.gz",
        ],
        strip_prefix = "PyYAML-3.12",
        sha256 = "592766c6303207a20efc445587778322d7f73b161bd994f227adaa341ba212ab",
    )

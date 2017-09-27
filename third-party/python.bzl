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

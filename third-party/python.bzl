#-*-python-*-

def guild_python_workspace():

    native.new_http_archive(
        name = "org_click",
        build_file = "//third-party:click.BUILD",
        urls = [
            "https://github.com/guildai/click/archive/1520fa44dcbe20ebed03f634ddfdffe48c46a799.zip"
        ],
        strip_prefix = "click-1520fa44dcbe20ebed03f634ddfdffe48c46a799",
        sha256 = "cdc599a630613e905770d5d4e87d67a160618541de565d0dc267f11202ca1670",
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

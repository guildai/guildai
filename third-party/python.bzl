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

    native.new_http_archive(
        name = "org_psutil",
        build_file = "//third-party:psutil.BUILD",
        urls = [
            "https://pypi.python.org/packages/d3/0a/74dcbb162554909b208e5dbe9f4e7278d78cc27470993e05177005e627d0/psutil-5.3.1.tar.gz"
        ],
        strip_prefix = "psutil-5.3.1",
        sha256 = "12dd9c8abbad15f055e9579130035b38617020ce176f4a498b7870e6321ffa67",
    )

    native.new_http_archive(
        name = "org_pip",
        build_file = "//third-party:pip.BUILD",
        urls = [
            "https://github.com/pypa/pip/archive/2243562b0e022b576bfdd9c08190657eab55a363.zip",
        ],
        strip_prefix = "pip-2243562b0e022b576bfdd9c08190657eab55a363",
        sha256 = "87e334e95f51e907604877fff07c50290b2f5d3a724b20795b1d112a68e41073",
    )

    native.new_http_archive(
        name = "org_setuptools",
        build_file = "//third-party:setuptools.BUILD",
        urls = [
            "https://pypi.python.org/packages/bd/4c/b06ab3abfc8bc93b87b70f4cab22352c3c72deba7b71390d14bfffa97c85/setuptools-36.6.0-py2.py3-none-any.whl",
        ],
        type = "zip",
        sha256 = "904356c95cf90e6fdc21915afafbc9ad3d11409c7afeee7c85156f469b353efb",
    )

    native.new_http_archive(
        name = "org_twine",
        build_file = "//third-party:twine.BUILD",
        urls = [
            "https://pypi.python.org/packages/f8/11/4fb94a084b49cd68eb831f97f3744a89d8bac505755bdcec84372cf21a68/twine-1.9.1-py2.py3-none-any.whl",
        ],
        type = "zip",
        sha256 = "d3ce5c480c22ccfb761cd358526e862b32546d2fe4bc93d46b5cf04ea3cc46ca",
    )

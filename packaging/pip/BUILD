package(default_visibility = ["//visibility:private"])

genrule(
    name = "linux",
    cmd = "$(location build-package) $(@D) manylinux1_x86_64",
    tools = [
        "build-package",
        # Hacking tools here to introduce a "data" like dependency for
        # our genrule. For some reason, listing //guild under srcs
        # only resolve to a single file.
        "//guild",
    ],
    srcs = [
        "LICENSE.txt",
        "MANIFEST.in",
        "README.rst",
        "setup.py",
    ],
    outs = [
        "guildai-0.1.0.post2-cp27-cp27mu-manylinux1_x86_64.whl",
    ],
)

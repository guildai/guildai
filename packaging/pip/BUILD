package(default_visibility = ["//visibility:private"])

genrule(
    name = "pip",
    cmd = "$(location build-package) $(@D)",
    tools = [
        "build-package",
        # Hacking tools here to introduce a "data" like dependency for
        # our genrule. For some reason, listing //guild under srcs
        # only resolve to a single file.
        "//guild",
    ],
    srcs = [
        "LICENSE",
        "MANIFEST.in",
        "README.rst",
        "setup.py",
    ],
    outs = [
        "guildai-0.1.0-py2-none-any.whl",
    ],
)

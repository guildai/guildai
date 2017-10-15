package(default_visibility = ["//visibility:private"])

filegroup(
    name = "pip",
    srcs = select({
        ":linux_x86_64": [":linux_whl"],
        ":darwin": [":darwin_whl"],
    }),
)

genrule(
    name = "linux_whl",
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
        "guildai-0.1.0.post2-cp35-cp35m-manylinux1_x86_64.whl",
    ],
)

genrule(
    name = "darwin_whl",
    cmd = "$(location build-package) $(@D)",
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
        "guildai-0.1.0.post2-cp27-cp27m-macosx_10_13_x86_64.whl",
        "guildai-0.1.0.post2-cp36-cp36m-macosx_10_13_x86_64.whl",
    ],
)

config_setting(
        name = "linux_x86_64",
        values = {"cpu": "k8"},
)

config_setting(
        name = "darwin",
        values = {"cpu": "darwin"},
)

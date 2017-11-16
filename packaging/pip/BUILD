package(default_visibility = ["//visibility:private"])

guild_version = "0.2.0.dev10"

filegroup(
    name = "pip",
    srcs = select({
        ":linux_x86_64": [":linux_whl"],
        ":darwin": [":darwin_whl"],
    }),
)

filegroup(
    name = "setup-srcs",
    srcs = [
        "LICENSE.txt",
        "MANIFEST.in",
        "setup.py",
    ],
)

genrule(
    name = "linux_whl",
    cmd = "$(location build-package) $(@D) manylinux1_x86_64",
    # These must be explicitly listed here as tools for bazel to build
    tools = [
        "//guild",
        "//guildai.dist-info",
        "build-package"
    ],
    srcs = [":setup-srcs"],
    outs = [
        "guildai-" + guild_version + "-cp27-cp27mu-manylinux1_x86_64.whl",
        "guildai-" + guild_version + "-cp35-cp35m-manylinux1_x86_64.whl",
    ],
)

genrule(
    name = "darwin_whl",
    cmd = "$(location build-package) $(@D)",
    # These must be explicitly listed here as tools for bazel to build
    tools = [
        "//guild",
        "//guildai.dist-info",
        "build-package"
    ],
    srcs = [":setup-srcs"],
    outs = [
        "guildai-" + guild_version + "-cp27-cp27m-macosx_10_13_x86_64.whl",
        "guildai-" + guild_version + "-cp36-cp36m-macosx_10_13_x86_64.whl",
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

package(default_visibility = ["//visibility:public"])

py_library(
    name = "tests",
    deps = [
        ":cpu-plugin",
        ":disk-plugin",
        ":imports",
        ":memory-plugin",
        ":op",
        ":project",
        ":plugin-python-utils",
        ":plugins",
        ":runs",
        ":tables",
        ":var",
    ],
)

py_library(
    name = "cpu-plugin",
    data = ["cpu-plugin.md"],
    deps = [
        "//guild/plugins",
        "//guild:plugin",
    ],
)

py_library(
    name = "disk-plugin",
    data = ["disk-plugin.md"],
    deps = [
        "//guild/plugins",
        "//guild:plugin",
    ],
)

py_library(
    name = "imports",
    data = ["imports.md"],
    deps = [
        # Intentially leaving empty - should catch missing modules.9
    ],
)

py_library(
    name = "memory-plugin",
    data = ["memory-plugin.md"],
    deps = [
        "//guild/plugins",
        "//guild:plugin",
    ],
)

py_library(
    name = "op",
    data = ["op.md"],
    deps = [
        "//guild:op",
        "//guild:project",
    ],
)

py_library(
    name = "plugin-python-utils",
    data = ["plugin-python-utils.md"] + glob(["samples/scripts/**"]),
    deps = [
        "//guild/plugins:python_util",
    ],
)

py_library(
    name = "plugins",
    data = ["plugins.md"],
    deps = [
        "//guild/plugins",
        "//guild:plugin",
    ],
)

py_library(
    name = "project",
    data = ["project.md"] + glob(["samples/projects/**"]),
    deps = [
        "//guild:project",
    ],
)

py_library(
    name = "runs",
    data = ["runs.md"] + glob(["samples/runs/**"]),
    deps = [
        "//guild:var",
    ],
)

py_library(
    name = "tables",
    data = ["tables.md"],
    deps = [
        "//guild:cli",
    ],
)

py_library(
    name = "var",
    data = ["var.md"],
    deps = [
        "//guild:var",
    ],
)

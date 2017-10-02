package(default_visibility = ["//visibility:public"])

py_library(
    name = "tests",
    deps = [
        ":op",
        ":project",
        ":plugins",
        ":runs",
        ":tables",
        ":var",
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

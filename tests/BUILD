package(default_visibility = ["//visibility:public"])

py_library(
    name = "tests",
    deps = [
        ":op",
        ":project",
        ":tables",
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
    name = "project",
    data = ["project.md"] + glob(["samples/projects/**"]),
    deps = [
        "//guild:project",
    ],
)

py_library(
    name = "tables",
    data = ["tables.md"],
    deps = [
        "//guild:cli",
    ],
)

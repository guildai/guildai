package(default_visibility = ["//visibility:public"])

py_library(
    name = "tests",
    deps = [
        ":dataframe",
        ":project",
        ":tables",
    ],
)

py_library(
    name = "dataframe",
    data = ["dataframe.md"],
    deps = [
        "@org_pandas",
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
        "//guild:table",
    ],
)

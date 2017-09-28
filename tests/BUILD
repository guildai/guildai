package(default_visibility = ["//visibility:public"])

py_library(
    name = "tests",
    deps = [
        ":project",
    ],
)

py_library(
    name = "project",
    data = ["project.md"] + glob(["samples/projects/**"]),
    deps = [
        "//guild:project",
    ],
)

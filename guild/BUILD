package(default_visibility = ["//visibility:public"])

sh_binary(
    name = "guild",
    srcs = ["//scripts:guild-exe"],
    data = [
        ":main",
    ]
)

py_library(
    name = "main",
    srcs = ["main.py"],
    deps = [
        "@org_click",
        ":check_cmd",
        ":run_cmd",
        ":runs_cmd",
        ":shell_cmd",
        ":sources_cmd",
    ]
)

py_library(
    name = "check_cmd",
    srcs = ["check_cmd.py"],
    data = [
        "//scripts:nvidia-tools-check",
        "//scripts:tensorflow-check",
    ],
    deps = [
        ":app",
        ":cli",
        ":test",
    ],
)

py_library(
    name = "app",
    srcs = ["app.py"],
    deps = [
        ":__init__",
    ]
)

py_library(
    name = "__init__",
    srcs = ["__init__.py"],
)

py_library(
    name = "cli",
    srcs = ["cli.py"],
    deps = [
        ":app",
    ],
)

py_library(
    name = "test",
    srcs = ["test.py"],
    data = [
        "//tests",
    ],
    deps = [
        ":app",
    ],
)

py_library(
    name = "run_cmd",
    srcs = ["run_cmd.py"],
    deps = [
        ":cli",
    ],
)

py_library(
    name = "runs_cmd",
    srcs = ["runs_cmd.py"],
    deps = [
        ":cli",
    ],
)

py_library(
    name = "project",
    srcs = ["project.py"],
    deps = [
        "@org_pyyaml",
    ]
)

py_library(
    name = "sources_cmd",
    srcs = ["sources_cmd.py"],
    deps = [
        ":config",
        ":cli",
        "@org_pandas",
    ],
)

py_library(
    name = "config",
    srcs = ["config.py"],
    deps = [
        ":var",
    ],
)

py_library(
    name = "var",
    srcs = ["var.py"],
    deps = [
    ],
)

py_library(
    name = "shell_cmd",
    srcs = ["shell_cmd.py"],
    deps = [
    ],
)


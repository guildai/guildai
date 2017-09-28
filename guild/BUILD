package(default_visibility = ["//visibility:public"])

sh_binary(
    name = "guild",
    srcs = ["//scripts:guild-exe"],
    data = [
        ":guild_main",
    ]
)

py_library(
    name = "guild_main",
    srcs = ["guild_main.py"],
    deps = [
        "@org_click",
        ":check_cmd",
        ":run_cmd",
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
    name = "project",
    srcs = ["project.py"],
    deps = [
        "@org_pyyaml",
    ]
)

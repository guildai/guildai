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
        ":models_cmd",
        ":operations_cmd",
        ":run_cmd",
        ":runs_cmd",
        ":shell_cmd",
        ":sources_cmd",
        ":view_cmd",
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
        "@org_click",
        ":plugin",
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
        ":cmd_support",
        ":op",
        ":project",
    ],
)

py_library(
    name = "runs_cmd",
    srcs = ["runs_cmd.py"],
    deps = [
        ":cli",
        ":cmd_support",
        ":var",
    ],
)

py_library(
    name = "project",
    srcs = ["project.py"],
    deps = [
        "@org_pyyaml",
        ":plugin",
    ]
)

py_library(
    name = "sources_cmd",
    srcs = ["sources_cmd.py"],
    deps = [
        ":config",
        ":cli",
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
        ":run",
        ":util",
    ],
)

py_library(
    name = "shell_cmd",
    srcs = ["shell_cmd.py"],
    deps = [
    ],
)

py_library(
    name = "models_cmd",
    srcs = ["models_cmd.py"],
    deps = [
        ":cli",
        ":cmd_support",
    ],
)

py_library(
    name = "operations_cmd",
    srcs = ["operations_cmd.py"],
    deps = [
        ":cli",
        ":project",
    ],
)

py_library(
    name = "op",
    srcs = ["op.py"],
    deps = [
        ":util",
        ":run",
    ],
    data = [
        ":op_main",
    ],
)

py_library(
    name = "util",
    srcs = ["util.py"],
    deps = [
    ],
)

py_library(
    name = "cmd_support",
    srcs = ["cmd_support.py"],
    deps = [
        ":cli",
        ":project",
        ":util",
    ],
)

py_library(
    name = "run",
    srcs = ["run.py"],
    deps = [
         ":util",
    ],
)

py_library(
    name = "plugin",
    srcs = ["plugin.py"],
    deps = [
    ],
)

py_library(
    name = "view_cmd",
    srcs = ["view_cmd.py"],
    deps = [
        "@org_click",
        ":cli",
        ":runs_cmd",
        ":tensorboard",
        ":util",
    ],
)

py_library(
    name = "tensorboard",
    srcs = ["tensorboard.py"],
    data = [
        "@org_tensorflow_tensorboard//tensorboard",
    ],
    deps = [
    ],
)

py_library(
    name = "op_main",
    srcs = ["op_main.py"],
    deps = [
    ],
)

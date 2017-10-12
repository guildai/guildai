package(default_visibility = ["//visibility:public"])

sh_binary(
    name = "guild",
    srcs = ["//guild/scripts:guild"],
    data = [
        ":main_bootstrap",
    ]
)

###################################################################
# Core modules
###################################################################

py_library(
    name = "__init__",
    srcs = ["__init__.py"],
    data = ["__guild_op_package__"],
)

py_library(
    name = "main_bootstrap",
    srcs = ["main_bootstrap.py"],
    deps = [
        ":main",
    ]
)

py_library(
    name = "main",
    srcs = ["main.py"],
    deps = [
        "@org_click",
        ":click_util",
        ":main_cmd",
    ]
)

py_library(
    name = "main_cmd",
    srcs = [
        "main_cmd.py",
        "main_cmd_impl.py",
    ],
    deps = [
        "@org_click",
        ":log",
        ":namespace",
        ":plugin",
        ":click_util",
        ":check_cmd",
        ":install_cmd",
        ":models_cmd",
        ":operations_cmd",
        ":packages_cmd",
        ":run_cmd",
        ":runs_cmd",
        ":shell_cmd",
        ":train_cmd",
        ":view_cmd",
    ]
)

###################################################################
# Commands
###################################################################

py_library(
    name = "check_cmd",
    srcs = [
        "check_cmd.py",
        "check_cmd_impl.py",
    ],
    data = [
        "//guild/scripts:nvidia-tools-check",
        "//guild/scripts:tensorflow-check",
    ],
    deps = [
        "@org_click",
        ":click_util",
        ":app",
        ":cli",
        ":test",
    ],
)

py_library(
    name = "install_cmd",
    srcs = [
        "install_cmd.py",
        "install_cmd_impl.py",
    ],
    deps = [
        "@org_click",
        ":cmd_support",
        ":click_util",
        ":pip_util"
    ],
)

py_library(
    name = "models_cmd",
    srcs = [
        "models_cmd.py",
        "models_cmd_impl.py",
    ],
    deps = [
        "@org_click",
        ":click_util",
        ":cli",
        ":cmd_support",
    ],
)

py_library(
    name = "operations_cmd",
    srcs = [
        "operations_cmd.py",
        "operations_cmd_impl.py",
    ],
    deps = [
        "@org_click",
        ":click_util",
        ":cli",
        ":cmd_support",
        ":project",
    ],
)

py_library(
    name = "packages_cmd",
    srcs = [
        "packages_cmd.py",
        "packages_cmd_impl.py",
    ],
    deps = [
        "@org_click",
        ":cli",
        ":click_util",
        ":package",
        ":pip_util",
    ],
)

py_library(
    name = "run_cmd",
    srcs = [
        "run_cmd.py",
        "run_cmd_impl.py",
    ],
    deps = [
        "@org_click",
        ":click_util",
        ":cli",
        ":cmd_support",
        ":op",
        ":project",
    ],
)

py_library(
    name = "runs_cmd",
    srcs = [
        "runs_cmd.py",
        "runs_cmd_impl.py",
    ],
    deps = [
        "@org_click",
        ":click_util",
        ":cmd_support",
        ":var",
    ],
)

py_library(
    name = "shell_cmd",
    srcs = [
        "shell_cmd.py",
        "shell_cmd_impl.py",
    ],
    deps = [
        "@org_click",
        ":click_util",
    ],
)

py_library(
    name = "train_cmd",
    srcs = ["train_cmd.py"],
    deps = [
        "@org_click",
        ":click_util",
        ":run_cmd",
    ],
)

py_library(
    name = "view_cmd",
    srcs = [
        "view_cmd.py",
        "view_cmd_impl.py",
    ],
    deps = [
        "@org_click",
        ":click_util",
        ":cli",
        ":runs_cmd",
        ":tensorboard",
        ":util",
    ],
)

###################################################################
# API
###################################################################

py_library(
    name = "app",
    srcs = ["app.py"],
    deps = [
        ":__init__",
    ]
)

py_library(
    name = "cli",
    srcs = ["cli.py"],
    deps = [
        "@org_click",
    ],
)

py_library(
    name = "click_util",
    srcs = ["click_util.py"],
    deps = [
        "@org_click",
    ]
)

py_library(
    name = "cmd_support",
    srcs = ["cmd_support.py"],
    deps = [
        ":cli",
        ":click_util",
        ":package",
        ":project",
        ":util",
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
    name = "log",
    srcs = ["log.py"],
    deps = [
    ],
)

py_library(
    name = "namespace",
    srcs = ["namespace.py"],
    deps = [
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
    name = "op_main",
    srcs = ["op_main.py"],
    deps = [
        ":log",
        ":plugin",
    ],
)

py_library(
    name = "package",
    srcs = ["package.py"],
    deps = [
        ":namespace",
    ],
)

py_library(
    name = "pip_util",
    srcs = ["pip_util.py"],
    deps = [
        "@org_pip",
        ":var",
    ],
)

py_library(
    name = "plugin",
    srcs = ["plugin.py"],
    deps = [
    ],
)

py_library(
    name = "plugin_util",
    srcs = ["plugin_util.py"],
    deps = [
        ":run",
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
    name = "run",
    srcs = ["run.py"],
    deps = [
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
    name = "test",
    srcs = ["test.py"],
    data = [
        "//guild/tests",
    ],
    deps = [
        ":app",
    ],
)

py_library(
    name = "util",
    srcs = ["util.py"],
    deps = [
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

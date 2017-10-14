package(default_visibility = ["//visibility:public"])

py_library(
    name = "main_cmd",
    srcs = [
        "main_cmd.py",
        "main_cmd_impl.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:__init__",
        "//guild:log",
        "//guild:namespace",
        "//guild:plugin",
        "//guild:click_util",
        ":check_cmd",
        ":install_cmd",
        ":models_cmd",
        ":operations_cmd",
        ":package_cmd",
        ":packages_cmd",
        ":run_cmd",
        ":runs_cmd",
        ":shell_cmd",
        ":train_cmd",
        ":uninstall_cmd",
        ":view_cmd",
    ]
)

py_library(
    name = "check_cmd",
    srcs = [
        "check_cmd.py",
        "check_cmd_impl.py",
        "tensorflow_info_main.py"
    ],
    deps = [
        "//third_party:click",
        "//third_party:setuptools",
        "//guild:__init__",
        "//guild:click_util",
        "//guild:cli",
        "//guild:test",
    ],
)

py_library(
    name = "install_cmd",
    srcs = [
        "install_cmd.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":packages_cmd",
    ],
)

py_library(
    name = "models_cmd",
    srcs = [
        "models_cmd.py",
        "models_cmd_impl.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:cli",
        "//guild:cmd_support",
    ],
)

py_library(
    name = "operations_cmd",
    srcs = [
        "operations_cmd.py",
        "operations_cmd_impl.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:cli",
        "//guild:cmd_support",
        "//guild:project",
    ],
)

py_library(
    name = "package_cmd",
    srcs = [
        "package_cmd.py",
        "package_cmd_impl.py",

    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:cmd_support",
        "//guild:package",
    ],
)

py_library(
    name = "packages_cmd",
    srcs = [
        "packages_cmd.py",
        "packages_cmd_impl.py",
        "packages_delete_cmd.py",
        "packages_info_cmd.py",
        "packages_list_cmd.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:cli",
        "//guild:click_util",
        "//guild:cmd_support",
        "//guild:package",
        "//guild:pip_util",
    ],
)

py_library(
    name = "run_cmd",
    srcs = [
        "run_cmd.py",
        "run_cmd_impl.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:cli",
        "//guild:cmd_support",
        "//guild:op",
        "//guild:project",
    ],
)

py_library(
    name = "runs_cmd",
    srcs = [
        "runs_cmd.py",
        "runs_cmd_impl.py",
        "runs_cmd_support.py",
        "runs_delete_cmd.py",
        "runs_info_cmd.py",
        "runs_list_cmd.py",
        "runs_restore_cmd.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:cmd_support",
        "//guild:var",
    ],
)

py_library(
    name = "shell_cmd",
    srcs = [
        "shell_cmd.py",
        "shell_cmd_impl.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:util",
    ],
)

py_library(
    name = "train_cmd",
    srcs = ["train_cmd.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":run_cmd",
    ],
)

py_library(
    name = "uninstall_cmd",
    srcs = [
        "uninstall_cmd.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":package_cmd",
    ],
)

py_library(
    name = "view_cmd",
    srcs = [
        "view_cmd.py",
        "view_cmd_impl.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:cli",
        "//guild:tensorboard",
        "//guild:util",
        ":runs_cmd",
    ],
)

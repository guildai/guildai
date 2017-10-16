package(default_visibility = ["//visibility:public"])

py_library(
    name = "main",
    srcs = [
        "main.py",
        "main_impl.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:__init__",
        "//guild:log",
        "//guild:namespace",
        "//guild:plugin",
        "//guild:click_util",
        ":check",
        ":install",
        ":models",
        ":operations",
        ":package",
        ":packages",
        ":run",
        ":runs",
        ":shell",
        ":train",
        ":uninstall",
        ":view",
    ]
)

py_library(
    name = "check",
    srcs = [
        "check.py",
        "check_impl.py",
        "tensorflow_info_main.py"
    ],
    deps = [
        "//third_party:click",
        "//third_party:setuptools",
        "//guild:__init__",
        "//guild:click_util",
        "//guild:cli",
        "//guild:plugin",
        "//guild:test",
        "//guild:util",
    ],
)

py_library(
    name = "install",
    srcs = [
        "install.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":packages",
    ],
)

py_library(
    name = "models",
    srcs = [
        "models.py",
        "models_impl.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:cli",
        "//guild:cmd_support",
    ],
)

py_library(
    name = "operations",
    srcs = [
        "operations.py",
        "operations_impl.py",
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
    name = "package",
    srcs = [
        "package.py",
        "package_impl.py",

    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:cmd_support",
        "//guild:package",
    ],
)

py_library(
    name = "packages",
    srcs = [
        "packages.py",
        "packages_impl.py",
        "packages_delete.py",
        "packages_info.py",
        "packages_list.py",
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
    name = "run",
    srcs = [
        "run.py",
        "run_impl.py",
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
    name = "runs",
    srcs = [
        "runs.py",
        "runs_impl.py",
        "runs_support.py",
        "runs_delete.py",
        "runs_info.py",
        "runs_list.py",
        "runs_purge.py",
        "runs_restore.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:cli",
        "//guild:click_util",
        "//guild:cmd_support",
        "//guild:var",
    ],
)

py_library(
    name = "shell",
    srcs = [
        "shell.py",
        "shell_impl.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:util",
    ],
)

py_library(
    name = "train",
    srcs = ["train.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":run",
    ],
)

py_library(
    name = "uninstall",
    srcs = [
        "uninstall.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":package",
    ],
)

py_library(
    name = "view",
    srcs = [
        "view.py",
        "view_impl.py",
    ],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        "//guild:cli",
        "//guild:tensorboard",
        "//guild:util",
        ":runs",
    ],
)

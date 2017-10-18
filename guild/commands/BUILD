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
    srcs = ["check.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":check_impl",
    ],
)

py_library(
    name = "check_impl",
    srcs = ["check_impl.py"],
    deps = [
        "//third_party:click",
        "//third_party:setuptools",
        "//guild:__init__",
        "//guild:cli",
        "//guild:plugin",
        "//guild:test",
        "//guild:util",
        ":tensorflow_info_main",
    ],
)

py_library(
    name = "install",
    srcs = ["install.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":packages_impl",
    ],
)

py_library(
    name = "models",
    srcs = ["models.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":models_impl",
    ],
)

py_library(
    name = "models_impl",
    srcs = ["models_impl.py"],
    deps = [
        "//guild:cli",
        "//guild:cmd_impl_support",
    ],
)

py_library(
    name = "operations",
    srcs = ["operations.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":operations_impl",
    ],
)

py_library(
    name = "operations_impl",
    srcs = ["operations_impl.py"],
    deps = [
        "//guild:cli",
        "//guild:cmd_impl_support",
        "//guild:modelfile",
    ],
)

py_library(
    name = "package",
    srcs = ["package.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":package_impl",
    ],
)

py_library(
    name = "package_impl",
    srcs = ["package_impl.py"],
    deps = [
        "//guild:cmd_impl_support",
        "//guild:package",
    ],
)

py_library(
    name = "packages",
    srcs = ["packages.py"],
    deps = [
        "//third_party:click",
        ":packages_delete",
        ":packages_info",
        ":packages_list",
    ],
)

py_library(
    name = "packages_delete",
    srcs = ["packages_delete.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":packages_impl",
    ],
)

py_library(
    name = "packages_impl",
    srcs = ["packages_impl.py"],
    deps = [
        "//guild:cli",
        "//guild:cmd_impl_support",
        "//guild:package",
        "//guild:pip_util",
    ],
)

py_library(
    name = "packages_info",
    srcs = ["packages_info.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":packages_impl",
    ],
)

py_library(
    name = "packages_list",
    srcs = ["packages_list.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":packages_impl",
    ],
)

py_library(
    name = "run",
    srcs = ["run.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":run_impl",
    ],
)

py_library(
    name = "run_impl",
    srcs = ["run_impl.py"],
    deps = [
        "//guild:cli",
        "//guild:cmd_impl_support",
        "//guild:modelfile",
        "//guild:op",
    ],
)

py_library(
    name = "runs",
    srcs = ["runs.py"],
    deps = [
        "//third_party:click",
        "//guild:cli",
        ":runs_delete",
        ":runs_info",
        ":runs_list",
        ":runs_purge",
        ":runs_restore",
        ":runs_support",
    ],
)

py_library(
    name = "runs_delete",
    srcs = ["runs_delete.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":runs_impl",
        ":runs_support",
    ],
)

py_library(
    name = "runs_impl",
    srcs = ["runs_impl.py"],
    deps = [
        "//guild:click_util",
        "//guild:cmd_impl_support",
        "//guild:var",
    ],
)

py_library(
    name = "runs_info",
    srcs = ["runs_info.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":runs_impl",
        ":runs_support",
    ],
)

py_library(
    name = "runs_list",
    srcs = ["runs_list.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":runs_impl",
        ":runs_support",
    ],
)

py_library(
    name = "runs_purge",
    srcs = ["runs_purge.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":runs_impl",
        ":runs_support",
    ],
)

py_library(
    name = "runs_restore",
    srcs = ["runs_restore.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":runs_impl",
        ":runs_support",
    ],
)

py_library(
    name = "runs_support",
    srcs = ["runs_support.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
    ],
)

py_library(
    name = "shell",
    srcs = ["shell.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":shell_impl",
    ],
)

py_library(
    name = "shell_impl",
    srcs = ["shell_impl.py"],
    deps = [
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
    name = "tensorflow_info_main",
    srcs = ["tensorflow_info_main.py"],
    deps = [
        "//third_party:click",
        # Does not depend on //third_party:tensorflow as it
        # handles cases where TF is not installed.
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
    srcs = ["view.py"],
    deps = [
        "//third_party:click",
        "//guild:click_util",
        ":runs_support",
        ":view_impl",
    ],
)

py_library(
    name = "view_impl",
    srcs = ["view_impl.py"],
    deps = [
        "//guild:cli",
        "//guild:tensorboard",
        "//guild:util",
        ":runs_impl",
    ],
)

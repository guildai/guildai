package(default_visibility = ["//visibility:public"])

py_library(
    name = "tests",
    deps = [
        ":cpu-plugin",
        ":config",
        ":dependencies",
        ":disk-plugin",
        ":entry-points",
        ":imports",
        ":logging",
        ":memory-plugin",
        ":modelfiles",
        ":models",
        ":namespaces",
        ":ops",
        ":packages",
        ":plugin-python-utils",
        ":plugins",
        ":runs",
        ":tables",
        ":utils",
        ":var",
    ],
)

py_library(
    name = "cpu-plugin",
    data = ["cpu-plugin.md"],
    deps = [
        "//guild/plugins:cpu",
        "//guild:plugin",
    ],
)

py_library(
    name = "config",
    data = ["config.md"],
    deps = [
        "//guild:config",
    ],
)

py_library(
    name = "dependencies",
    data = ["dependencies.md"],
    deps = [
        "//guild:deps",
        "//guild:modelfile",
   ],
)

py_library(
    name = "disk-plugin",
    data = ["disk-plugin.md"],
    deps = [
        "//guild/plugins:disk",
        "//guild:plugin",
    ],
)

py_library(
    name = "entry-points",
    data = ["entry-points.md"],
    deps = [
        "//third_party:setuptools",
        "//guild/plugins",
   ],
)

py_library(
    name = "imports",
    data = ["imports.md"],
    deps = [
        "//guild:__init__",
    ],
)

py_library(
    name = "logging",
    data = ["logging.md"],
    deps = [
        "//guild:log",
    ],
)

py_library(
    name = "memory-plugin",
    data = ["memory-plugin.md"],
    deps = [
        "//guild/plugins:memory",
        "//guild:plugin",
    ],
)

py_library(
    name = "modelfiles",
    data = ["modelfiles.md"] + glob(["samples/projects/**"]),
    deps = [
        "//guild:modelfile",
    ],
)

py_library(
    name = "models",
    data = ["models.md"],
    deps = [
    ],
)

py_library(
    name = "namespaces",
    data = ["namespaces.md"],
    deps = [
        "//guild:namespace",
    ],
)

py_library(
    name = "ops",
    data = ["ops.md"],
    deps = [
        "//guild:op",
        "//guild:modelfile",
    ],
)

py_library(
    name = "packages",
    data = ["packages.md"],
    deps = [
        "//guild:package",
    ],
)

py_library(
    name = "plugin-python-utils",
    data = ["plugin-python-utils.md"] + glob(["samples/scripts/**"]),
    deps = [
        "//guild/plugins:python_util",
    ],
)

py_library(
    name = "plugins",
    data = ["plugins.md"],
    deps = [
        "//guild/plugins",
        "//guild:plugin",
    ],
)

py_library(
    name = "runs",
    data = ["runs.md"] + glob(["samples/runs/**"]),
    deps = [
        "//guild:var",
    ],
)

py_library(
    name = "tables",
    data = ["tables.md"],
    deps = [
        "//guild:cli",
    ],
)

py_library(
    name = "utils",
    data = ["utils.md"],
    deps = [
        "//guild:util",
    ],
)

py_library(
    name = "var",
    data = ["var.md"],
    deps = [
        "//guild:var",
    ],
)

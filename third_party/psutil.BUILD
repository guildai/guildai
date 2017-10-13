py_library(
    name = "org_psutil",
    srcs = glob(["psutil/*.py"]),
    visibility = ["//visibility:public"],
    data = [
        #":psutil_native_darwin",
        ":psutil_native_linux",
    ],
)

psutil_srcs = glob([
        "setup.py",
        "README.rst",
        "**/*.py",
        "**/*.c",
        "**/*.h",
])

psutil_native_cmd = (
    "pushd `dirname $(location setup.py)` && " +
    "python2 setup.py build_ext -i && " +
    "python3 setup.py build_ext -i && " +
    "popd && " +
    "cp `dirname $(location setup.py)`/psutil/*.so $(@D)/psutil/"
)

"""
genrule(
    name = "psutil_native_darwin",
    srcs = psutil_srcs,
    outs = [
        "psutil/_psutil_osx.so",
        "psutil/_psutil_posix.so",
        "psutil/_psutil_osx.cpython-36m-darwin.so",
        "psutil/_psutil_posix.cpython-36m-darwin.so",
    ],
    cmd = psutil_native_cmd,
)
"""

genrule(
    name = "psutil_native_linux",
    srcs = psutil_srcs,
    outs = [
        "psutil/_psutil_linux.so",
        "psutil/_psutil_posix.so",
        "psutil/_psutil_linux.cpython-35m-x86_64-linux-gnu.so",
        "psutil/_psutil_posix.cpython-35m-x86_64-linux-gnu.so",
    ],
    cmd = psutil_native_cmd,
)

config_setting(
    name = "darwin",
    values = {"cpu": "darwin"}
)

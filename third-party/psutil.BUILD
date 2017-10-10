py_library(
    name = "org_psutil",
    srcs = glob(["psutil/*.py"]),
    visibility = ["//visibility:public"],
    data = [
        ":psutil_native",
        ":guild_op_package_marker"
    ],
)

genrule(
    name = "psutil_native",
    srcs = glob([
        "setup.py",
        "README.rst",
        "psutil/*.py",
        "psutil/*.c",
        "psutil/*.h",
    ]),
    outs = [
        "psutil/_psutil_linux.so",
        "psutil/_psutil_posix.so",
        "psutil/_psutil_linux.cpython-35m-x86_64-linux-gnu.so",
        "psutil/_psutil_posix.cpython-35m-x86_64-linux-gnu.so",
    ],
    cmd = (
        "pushd `dirname $(location setup.py)` && " +
        "python2 setup.py build_ext -i && " +
        "python3 setup.py build_ext -i && " +
        "popd && " +
        "cp `dirname $(location setup.py)`/psutil/*.so $(@D)/psutil/"
    )
)

genrule(
    name = "guild_op_package_marker",
    outs = ["psutil/__guild_op_package__"],
    # Not sure why $(@D) here is pointing to 'psutil/' whereas it's
    # pointing to 'psutil/..' in the psutil_native rule but this is
    # the case.
    cmd = (
        "touch $(@D)/__guild_op_package__"
    )
)

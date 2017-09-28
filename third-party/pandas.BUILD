py_library(
    name = "org_pandas",
    srcs = glob(
        include=["pandas/**/*.py"],
        exclude=["pandas/test/**"]
    ),
    visibility = ["//visibility:public"],
    data = [":pandas_native"],
)

genrule(
    name = "pandas_native",
    srcs = glob([
        "setup.py",
        "setup.cfg",
        "pandas/**/*.py",
        "pandas/**/*.h",
        "pandas/**/*.c",
        "pandas/**/*.cpp",
    ]),
    outs = [
        "pandas/_libs/algos.so",
        "pandas/_libs/groupby.so",
        "pandas/_libs/hashing.so",
        "pandas/_libs/hashtable.so",
        "pandas/_libs/index.so",
        "pandas/_libs/interval.so",
        "pandas/_libs/join.so",
        "pandas/_libs/json.so",
        "pandas/_libs/lib.so",
        "pandas/_libs/parsers.so",
        "pandas/_libs/period.so",
        "pandas/_libs/reshape.so",
        "pandas/_libs/sparse.so",
        "pandas/_libs/testing.so",
        "pandas/_libs/tslib.so",
        "pandas/_libs/window.so",
        "pandas/io/msgpack/_packer.so",
        "pandas/io/msgpack/_unpacker.so",
        "pandas/io/sas/_sas.so",
        "pandas/util/_move.so",
        "pandas/_libs/algos.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/groupby.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/hashing.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/hashtable.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/index.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/interval.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/join.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/json.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/lib.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/parsers.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/period.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/reshape.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/sparse.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/testing.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/tslib.cpython-35m-x86_64-linux-gnu.so",
        "pandas/_libs/window.cpython-35m-x86_64-linux-gnu.so",
        "pandas/io/msgpack/_packer.cpython-35m-x86_64-linux-gnu.so",
        "pandas/io/msgpack/_unpacker.cpython-35m-x86_64-linux-gnu.so",
        "pandas/io/sas/_sas.cpython-35m-x86_64-linux-gnu.so",
        "pandas/util/_move.cpython-35m-x86_64-linux-gnu.so",
    ],
    cmd = (
        "pushd `dirname $(location setup.py)` && " +
        "python2 setup.py build_ext -i && " +
        "python3 setup.py build_ext -i && " +
        "popd && " +
        "cp `dirname $(location setup.py)`/pandas/_libs/*.so $(@D)/pandas/_libs && " +
        "cp `dirname $(location setup.py)`/pandas/io/msgpack/*.so $(@D)/pandas/io/msgpack && " +
        "cp `dirname $(location setup.py)`/pandas/io/sas/*.so $(@D)/pandas/io/sas && " +
        "cp `dirname $(location setup.py)`/pandas/util/*.so $(@D)/pandas/util"
    )
)

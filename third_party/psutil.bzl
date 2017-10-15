def psutil_ext_cmd(py_cmd, output_path):
    return (
        "setup_dir=`dirname $(location setup.py)` && " +
        "output_dir=$(@D)/%s && " +
        "pushd $$setup_dir && " +
        "%s setup.py build_ext -i && " +
        "popd && " +
        "cp $$setup_dir/psutil/*.so $$output_dir && " +
        "echo '==================================================================='; " +
        "echo 'psutil build_ext output'; " +
        "echo '==================================================================='; " +
        "ls $$output_dir; " +
        "echo '==================================================================='"
    ) % (output_path, py_cmd)

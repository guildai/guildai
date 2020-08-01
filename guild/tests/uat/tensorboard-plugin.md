# TensorBoard Plugin

The TensorBoard plugin API insulates Guild from the ever-changing
TensorBoard interface. These tests run across various versions of
TensorBoard to confirm expected functionality.

For these tests we use virtual environments to test specific
TensorBoard versions.

    >>> def mkenv():
    ...     tmp = mkdtemp()
    ...     if sys.version_info[0] == 2:
    ...         quiet("virtualenv --python python2 %s" % tmp)
    ...     else:
    ...         quiet("python -m venv %s" % tmp)
    ...     return tmp

    >>> def pip_install(req, venv_dir):
    ...     quiet("%s/bin/python -m pip install '%s'" % (venv_dir, req))

    >>> def tensorboard_check(venv):
    ...     python_path = path(_python_lib_dir(venv), "site-packages")
    ...     print("python_path: %s" % python_path)
    ...     run("PYTHONPATH='%s' guild tensorboard --check" % python_path)

    >>> def _python_lib_dir(venv):
    ...     venv_lib_dir_names = dir(path(venv, "lib"))
    ...     assert venv_lib_dir_names, venv
    ...     python_lib_dir = venv_lib_dir_names[0]
    ...     assert python_lib_dir.startswith("python"), (venv, venv_lib_dir_names)
    ...     return path(venv, "lib", python_lib_dir)

## tensorboard<2

Guild no longer supports TensorBoard versions prior to 2.0.0.

    >>> venv = mkenv()
    >>> pip_install("tensorboard<2", venv)
    >>> tensorboard_check(venv)
    python_path: ...
    version: 1.15.0
    supported: no
    <exit 0>

## tensorboard<2.1

    >>> venv = mkenv()
    >>> pip_install("tensorboard<2.1", venv)
    >>> tensorboard_check(venv)

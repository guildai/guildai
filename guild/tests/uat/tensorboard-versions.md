# TensorBoard Plugin

The TensorBoard plugin API insulates Guild from the ever-changing
TensorBoard interface. These tests run across various versions of
TensorBoard to confirm expected functionality.

For these tests we use virtual environments to test specific
TensorBoard versions.

    >>> def mkenv():
    ...     venv = mkdtemp()
    ...     print("venv: %s" % venv)
    ...     if sys.version_info[0] == 2:
    ...         quiet("virtualenv --python python2 %s" % venv)
    ...     else:
    ...         quiet("python -m venv %s" % venv)
    ...     return venv

    >>> def pip_install(req, venv_dir):
    ...     quiet("%s/bin/python -m pip install -U '%s'" % (venv_dir, req))

    >>> def tensorboard_check(req, venv):
    ...     python_path = path(_python_lib_dir(venv), "site-packages")
    ...     print("python_path: %s" % python_path)
    ...     run("PYTHONPATH='%s' guild check -nt %s.md" % (python_path, req))

    >>> def _python_lib_dir(venv):
    ...     venv_lib_dir_names = dir(path(venv, "lib"))
    ...     assert venv_lib_dir_names, venv
    ...     python_lib_dir = venv_lib_dir_names[0]
    ...     assert python_lib_dir.startswith("python"), (venv, venv_lib_dir_names)
    ...     return path(venv, "lib", python_lib_dir)

    >>> def check(req):
    ...     venv = mkenv()
    ...     pip_install("pip", venv)
    ...     pip_install(req, venv)
    ...     tensorboard_check(req, venv)

## 2.0.0

    >>> check("tensorboard==2.0.0")
    venv: ...
    python_path: ...
    internal tests:
      tensorboard==2.0.0.md:       ok
    <exit 0>

## 2.1.0

    >>> check("tensorboard==2.1.0")
    venv: ...
    python_path: ...
    internal tests:
      tensorboard==2.1.0.md:       ok
    <exit 0>

## 2.2.0

    >>> check("tensorboard==2.2.0")  # doctest: -PY2
    venv: ...
    python_path: ...
    internal tests:
      tensorboard==2.2.0.md:       ok
    <exit 0>

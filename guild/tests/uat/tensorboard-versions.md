# TensorBoard Plugin

The TensorBoard plugin API insulates Guild from the ever-changing
TensorBoard interface. These tests run across various versions of
TensorBoard to confirm expected functionality.

For these tests we use virtual environments to test specific
TensorBoard versions.

    >>> def mkenv():
    ...     venv = mkdtemp()
    ...     print("venv: %s" % venv)
    ...     quiet("python -m venv %s" % venv)
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
    ...     pip_install("protobuf<4", venv)  # TEMP to workaround breakage in Google protobuf ecosystem
    ...     pip_install(req, venv)
    ...     tensorboard_check(req, venv)

## 2.7.0

    >>> check("tensorboard==2.7.0")  # doctest: -PY2 -PY3 +PY36 +PY37 +PY38 +PY39
    venv: ...
    python_path: ...
    internal tests:
      tensorboard==2.7.0.md:       ok...
    <exit 0>


## 2.8.0

    >>> check("tensorboard==2.8.0")  # doctest: -PY2
    venv: ...
    python_path: ...
    internal tests:
      tensorboard==2.8.0.md:       ok...
    <exit 0>

## 2.9.0

    >>> check("tensorboard==2.9.0")  # doctest: -PY2
    venv: ...
    python_path: ...
    internal tests:
      tensorboard==2.9.0.md:       ok...
    <exit 0>

## 2.9.1

    >>> check("tensorboard==2.9.1")  # doctest: -PY2
    venv: ...
    python_path: ...
    internal tests:
      tensorboard==2.9.1.md:       ok...
    <exit 0>

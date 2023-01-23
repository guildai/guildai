import argparse
import doctest
import glob
import os
import subprocess
import sys
import tempfile


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--unused-code",
        action="store_true",
        help="Print unused code and exit",
    )
    args = p.parse_args()
    if args.unused_code:
        _unused_code()
    else:
        p.parse_args(["--help"])


def _unused_code():
    tmp = tempfile.mkdtemp(prefix="guild-tools-")
    print(f"Writing tests as Python modules to {tmp}")
    _write_test_code(tmp)
    _run_vulture_and_exit(tmp)


def _write_test_code(dest_dir):
    for test_file in _iter_test_files():
        py_file = _py_file_for_test(test_file)
        examples = _examples_for_test(test_file)
        py_file_dest = os.path.join(dest_dir, py_file)
        with open(py_file_dest, "w") as py_out:
            for example in examples:
                py_out.write(example.source)
                py_out.write("\n")


def _iter_test_files():
    for path in glob.glob("guild/tests/*.md"):
        yield path
    for path in glob.glob("guild/tests/uat/*.md"):
        yield path


def _py_file_for_test(test_file):
    assert test_file[-3:] == ".md", test_file
    return test_file.replace(os.path.sep, "_").replace("-", "_")[:-3] + ".py"


def _examples_for_test(test_file):
    _register_doctest_options()
    with open(test_file) as f:
        test_file_str = f.read()
    return doctest.DocTestParser().get_examples(test_file_str, name=test_file)


def _register_doctest_options():
    # Options are regstered in `guild._test`
    from guild import _test as _


def _run_vulture_and_exit(tests_dir):
    cmd = ["vulture", "setup.py", "tools.py", "guild", tests_dir]
    with subprocess.Popen(cmd, stdout=subprocess.PIPE) as p:
        for line in p.stdout:
            if not line:
                break
            line = line.decode()
            if tests_dir in line:
                continue
            sys.stdout.write(line)
            sys.stdout.flush()
    sys.exit(p.returncode)


if __name__ == "__main__":
    main()

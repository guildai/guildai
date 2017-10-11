import doctest
import glob
import logging
import os
import pprint
import re
import sys
import tempfile

class Py23DocChecker(doctest.OutputChecker):
    """Output checker that works around Python 2/3 unicode representations.

    https://dirkjan.ochtman.nl/writing/2014/07/06/single-source-python-23-doctests.html
    """

    def check_output(self, want, got, optionflags):
        if sys.version_info[0] > 2:
            want = re.sub("u'(.*?)'", "'\\1'", want)
            want = re.sub('u"(.*?)"', '"\\1"', want)
        return doctest.OutputChecker.check_output(self, want, got, optionflags)

def run_all():
    return run(all_tests())

def all_tests():
    test_pattern = os.path.join(tests_dir(), "*.md")
    return sorted(
        [_test_name_from_path(path)
         for path in glob.glob(test_pattern)])

def tests_dir():
    return os.path.join(os.path.dirname(__file__), "tests")

def _test_name_from_path(path):
    name, _ = os.path.splitext(os.path.basename(path))
    return name

def run(tests):
    sys.stdout.write("internal tests:\n")
    success = True
    for test in tests:
        run_success = _run_test(test)
        success = success and run_success
    return success

def _run_test(name):
    sys.stdout.write("  %s:" % name)
    try:
        failures, _tests = _run_test_file(_test_filename(name))
    except IOError:
        sys.stdout.write(" ERROR test not found\n")
        return False
    else:
        if not failures:
            sys.stdout.write(" " * (23 - len(name)))
            sys.stdout.write(" ok\n")
        return failures == 0

def _test_filename(name):
    # Path must be relative to module
    return os.path.join("tests", name + ".md")

def _run_test_file(filename):
    return _run_test_file_with_config(
        filename,
        globs=test_globals(),
        optionflags=(
            doctest.REPORT_ONLY_FIRST_FAILURE |
            doctest.ELLIPSIS |
            doctest.IGNORE_EXCEPTION_DETAIL |
            doctest.NORMALIZE_WHITESPACE))

def _run_test_file_with_config(filename, globs, optionflags):
    """Modified from doctest.py to use custom checker."""

    text, filename = _load_testfile(filename)
    name = os.path.basename(filename)

    if globs is None:
        globs = {}
    else:
        globs = globs.copy()
    if '__name__' not in globs:
        globs['__name__'] = '__main__'

    checker = Py23DocChecker()
    runner = doctest.DocTestRunner(
        checker=checker,
        verbose=None,
        optionflags=optionflags)

    parser = doctest.DocTestParser()
    test = parser.get_doctest(text, globs, name, filename, 0)
    runner.run(test)

    runner.summarize()

    if doctest.master is None:
        doctest.master = runner
    else:
        doctest.master.merge(runner)

    return doctest.TestResults(runner.failures, runner.tries)

def _load_testfile(filename):
    # Wrapper to handle Python 2/3 differences
    # pylint: disable=protected-access
    try:
        # pylint: disable=no-value-for-parameter
        return doctest._load_testfile(filename, None, True)
    except TypeError:
        # pylint: disable=too-many-function-args
        return doctest._load_testfile(filename, None, True, "utf-8")

def test_globals():
    return {
        "cat": cat,
        "LogCapture": LogCapture,
        "find": find,
        "mkdtemp": mkdtemp,
        "pprint": pprint.pprint,
        "sample": sample,
        "samples_dir": samples_dir
    }

def sample(name):
    return os.path.join(samples_dir(), name)

def samples_dir():
    return os.path.join(tests_dir(), "samples")

def mkdtemp():
    return tempfile.mkdtemp(prefix="guildtest-")

def find(root):
    all = []
    for path, _, files in os.walk(root):
        for name in files:
            full_path = os.path.join(path, name)
            rel_path = os.path.relpath(full_path, root)
            all.append(rel_path)
    all.sort()
    return all

def cat(file_path):
    with open(file_path, "r") as f:
        return f.read()

class LogCapture(object):

    def __init__(self):
        self._records = []

    def __enter__(self):
        logging.getLogger().addFilter(self)
        self._records = []

    def __exit__(self, *exc):
        logging.getLogger().removeFilter(self)

    def filter(self, record):
        self._records.append(record)

    def print_all(self):
        format = logging.getLogger().handlers[0].format
        for r in self._records:
            print(format(r))

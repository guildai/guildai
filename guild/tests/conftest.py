from doctest import ELLIPSIS, NORMALIZE_WHITESPACE
import os
from subprocess import check_output
import re
import platform

import pytest
from textwrap import dedent
from sybil import Sybil, Example
from sybil.parsers.codeblock import CodeBlockParser
from sybil.parsers.doctest import DocTestParser, DocTest

from guild import _test as gt

THIS_DIR = os.path.dirname(__file__)
os.environ["PYTEST_ONLY"] = "true"


def sybil_setup(namespace):
    for k, v in gt.test_globals().items():
        namespace[k] = v
    namespace["NORMALIZE_PATHS"] = gt.NORMALIZE_PATHS
    namespace["PYTEST_ONLY"] = gt.PYTEST_ONLY


class GuildDocTestParser(DocTestParser):
    def __init__(self, optionflags=0):
        super().__init__(optionflags)
        self.runner = gt.TestRunner(optionflags=optionflags)

    def evaluate(self, sybil_example: Example) -> str:
        example = sybil_example.parsed
        namespace = sybil_example.namespace

        example.want = example.want.replace("???", "...")
        example.want = example.want.replace(":<pathsep>", os.path.pathsep)

        output = []
        with gt.StderrCapture(autoprint=False):
            with gt.SysPath(prepend=[os.path.join(gt.tests_dir(), "external")]):
                self.runner.run(
                    DocTest(
                        [example],
                        namespace,
                        name=None,
                        filename=None,
                        lineno=example.lineno,
                        docstring=None,
                    ),
                    clear_globs=False,
                    out=output.append,
                )
        return ''.join(output)


def evaluate_bash(example: Example):
    command, expected = dedent(str(example.parsed)).strip().split('\n')
    actual = (
        check_output(command[2:].split(), cwd=os.path.dirname(example.path))
        .strip()
        .decode('ascii')
    )
    if expected.startswith("???"):
        actual = re.sub(".+[:]?\n", actual, "???:\n")
    assert actual == expected, repr(actual) + ' != ' + repr(expected)


optionflags = (
    gt._report_first_flag()
    | ELLIPSIS
    | NORMALIZE_WHITESPACE
    | gt.NORMALIZE_PATHS
    | gt.STRIP_U
    | gt.STRIP_L
    | gt.STRIP_ANSI_FMT
    | gt.PY3
    | gt.ANNOTATIONS
    | gt.PYTEST_ONLY
)

if platform.system() == "Windows":
    optionflags |= gt.WINDOWS_ONLY | gt.WINDOWS
elif platform.system() == "Darwin":
    optionflags |= gt.MACOS

pytest_collect_file = Sybil(
    path=".",
    excludes=["*/tests/samples/*", "*/tests/uat/*"],
    parsers=[
        GuildDocTestParser(optionflags=optionflags),
        CodeBlockParser(language="bash", evaluator=evaluate_bash),
    ],
    pattern='*.md',
    setup=sybil_setup,
).pytest()

# Copyright 2017-2018 TensorHub, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import difflib
import glob
import logging
import os
import re
import subprocess
import sys

import click

from guild import opref as opreflib
from guild import var

log = logging.getLogger("guild")

class TestError(Exception):
    pass

class Failed(TestError):
    pass

class RunConfig(object):

    def __init__(self, models=None, operations=None,
                 one_model=False, gpus=None):
        self.models = models or ()
        self.operations = operations or ()
        self.one_model = one_model
        self.gpus = gpus

    def op_matches_models(self, opspec):
        opref = opreflib.OpRef.from_string(opspec)
        return (
            self._filter_model(opref) and
            self._filter_op(opref))

    def _filter_model(self, opref):
        if not self.models:
            return True
        for m in self.models:
            if re.match(r"%s$" % m, opref.model_name):
                return True
        return False

    def _filter_op(self, opref):
        if not self.operations:
            return True
        for o in self.operations:
            if re.match(r"%s$" % o, opref.op_name):
                return True
        return False

class _CompareHelp(object):

    type_attr = "compare-help"

    def __init__(self, step_config, test):
        self.compare_to = _test_path(test, step_config[self.type_attr])
        self.guildfile_src = test.guildfile.src

    def run(self, _run_config):
        _status("Checking help in %s" % os.path.relpath(self.guildfile_src))
        help_out = _output(["guild", "help", self.guildfile_src])
        expected = _read(self.compare_to)
        _compare(help_out, expected, "<help>", self.compare_to)

class _RunOp(object):

    type_attr = "run"

    def __init__(self, step_config, test):
        self.guildfile = test.guildfile
        self.op_name = step_config[self.type_attr]
        self.disable_plugins = step_config.get("disable-plugins")
        self.flag_vals = step_config.get("flags") or {}
        self.expect = [
            _resolve_op_expect(expect, test)
            for expect in (step_config.get("expect") or [])]

    def run(self, run_config, model=None):
        op_spec = self._op_spec(model)
        if not run_config.op_matches_models(op_spec):
            log.info("Skipping operation %s", op_spec)
            return
        self._run_op(op_spec, run_config.gpus)
        self._check_expected()

    def _op_spec(self, model):
        if model:
            return "%s:%s" % (model, self.op_name)
        else:
            return self.op_name

    def _run_op(self, op_spec, gpus):
        _status("Running operation %s" % op_spec)
        _call(self._run_cmd(op_spec, gpus), cwd=self.guildfile.dir)

    def _run_cmd(self, op_name, gpus):
        cmd = ["guild", "run", "-y", op_name]
        if gpus:
            cmd.extend(["--gpus", gpus])
        elif gpus == "":
            cmd.append("--no-gpus")
        if self.disable_plugins:
            cmd.extend(["--disable-plugins", self.disable_plugins])
        for name, val in sorted(self.flag_vals.items()):
            cmd.append("%s=%s" % (name, val))
        return cmd

    def _check_expected(self):
        if not self.expect:
            return
        run_dir = _latest_run_dir()
        _status("Checking %s" % os.path.basename(run_dir))
        for expected in self.expect:
            expected.check(run_dir)

class _ForEachModel(object):

    type_attr = "for-each-model"

    def __init__(self, step_config, test):
        config = step_config[self.type_attr]
        self.models = self._init_models(config, test)
        self.steps = [
            _resolve_model_step(step, test)
            for step in (config.get("steps") or [])
            if not _step_disabled(step)]

    def _init_models(self, config, test):
        models = config.get("models")
        if not models:
            models = self._all_models(config, test)
        except_models = set(config.get("except") or [])
        return [m for m in models if m not in except_models]

    @staticmethod
    def _all_models(config, test):
        first = config.get("first")
        if not first:
            return sorted(test.guildfile.models)
        def sort_key(m):
            if m == first:
                return '\x00'
            return m
        return sorted(test.guildfile.models, key=sort_key)

    def run(self, run_config):
        for model in self.models:
            for step in self.steps:
                step.run(run_config, model=model)
            if run_config.one_model:
                break

class _ExpectFile(object):

    type_attr = "file"

    def __init__(self, step_config, test):
        self.path = step_config[self.type_attr]
        self.compare_to = _test_path(test, step_config.get("compare"))
        self.pattern = step_config.get("contains")
        self.pattern_re = _compile_pattern(self.pattern)

    def check(self, run_dir):
        _status("file: %s%s" % (self.path, self._status_qualifiers), False)
        path_glob = os.path.join(run_dir, self.path)
        matches = glob.glob(path_glob)
        if not matches:
            raise Failed("no files matching %s" % path_glob)
        for path in matches:
            self._check_path(path)

    def _check_path(self, path):
        if self.compare_to:
            _compare_files(path, self.compare_to)
        if self.pattern_re:
            out = _read_output(path)
            if not self.pattern_re.search(out):
                raise Failed(
                    "could not find pattern %r in %s"
                    % (self.pattern, path))

    @property
    def _status_qualifiers(self):
        quals = []
        if self.compare_to:
            quals.append("compare to %s" % self.compare_to)
        if self.pattern:
            quals.append("contains %r" % self.pattern)
        if not quals:
            return ""
        return " (%s)" % ", ".join(quals)

class _ExpectOutput(object):

    type_attr = "output"

    def __init__(self, step_config, _test):
        self.pattern = step_config[self.type_attr]
        self.pattern_re = _compile_pattern(self.pattern)

    def check(self, run_dir):
        _status("output: %s" % self.pattern, False)
        output_path = os.path.join(run_dir, ".guild", "output")
        out = _read_output(output_path)
        if not self.pattern_re.search(out):
            raise Failed(
                "could not find pattern %r in %s"
                % (self.pattern, output_path))

def run_guildfile_test(test, run_config=None):
    run_config = run_config or RunConfig()
    steps = [
        _resolve_step(step, test) for step in test.steps
        if not _step_disabled(step)]
    _status("Testing %s" % test.name)
    for step in steps:
        step.run(run_config)

def _step_disabled(step):
    return step.get("disabled") is True

def _resolve_step(step, test, step_classes=None, step_desc="test step"):
    if step_classes is None:
        step_classes = [
            _CompareHelp,
            _RunOp,
            _ForEachModel,
        ]
    for step_class in step_classes:
        if step_class.type_attr in step:
            return step_class(step, test)
    raise TestError("invalid %s: %r" % (step_desc, step))

def _resolve_model_step(step, test):
    return _resolve_step(step, test, [_RunOp], "for-each-model step")

def _status(msg, bold=True):
    click.echo(click.style(msg, bold=bold))

def _test_path(test, path):
    if path is None:
        return None
    return os.path.join(test.guildfile.dir, path)

def _output(cmd):
    log.debug("cmd: %r", cmd)
    try:
        out = subprocess.check_output(cmd)
    except subprocess.CalledProcessError as e:
        sys.stdout.write(e.output)
        sys.stdout.flush()
        raise Failed("command failed")
    else:
        return out.decode()

def _call(cmd, **kw):
    log.debug("cmd: %r", cmd)
    try:
        subprocess.check_call(cmd, **kw)
    except subprocess.CalledProcessError:
        raise Failed("command failed")

def _read(path):
    return open(path, "r").read()

def _compare(actual, expected, actual_src, expected_src):
    a = re.split(r"\n\r?", expected)
    b = re.split(r"\n\r?", actual)
    fromfile = expected_src
    tofile = actual_src
    diff = list(difflib.unified_diff(a, b, fromfile, tofile))
    if diff:
        sys.stderr.write("\n".join(diff))
        sys.stderr.write("\n")
        raise Failed("unexpected file contents")

def _compare_files(actual, expected):
    _compare(
        open(actual, "r").read(),
        open(expected, "r").read(),
        actual,
        expected)

def _latest_run_dir():
    latest = (None, 0)
    runs_dir = var.runs_dir()
    for name in os.listdir(runs_dir):
        path = os.path.join(runs_dir, name)
        mtime = os.stat(path).st_mtime
        if mtime > latest[1]:
            latest = (path, mtime)
    if latest[0] is None:
        raise TestError("expected at least one run in %s" % runs_dir)
    return latest[0]

def _resolve_op_expect(expect, test):
    expect_classes = [_ExpectFile, _ExpectOutput]
    for expect_class in expect_classes:
        if expect_class.type_attr in expect:
            return expect_class(expect, test)
    raise TestError("invalid expect config: %r" %  expect)

def _compile_pattern(pattern):
    if pattern is None:
        return None
    try:
        return re.compile(pattern)
    except Exception:
        raise TestError("invalid regular expression: %r" % pattern)

def _read_output(path):
    try:
        return open(path, "r").read()
    except Exception:
        raise Failed("error reading run output from %s" % path)

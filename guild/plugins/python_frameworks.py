# Copyright 2017-2023 Posit Software, PBC
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

import os
import re

from guild import config
from guild import op_util
from guild import plugin as pluginlib
from guild import python_util
from guild import summary

from .python_script import PythonScriptModelProxy
from .python_script import PythonScriptOpdefSupport


class Keras:
    name = "keras"

    output_scalars = [
        r"Epoch (?P<step>[0-9]+)",
        r" - ([a-z_]+): (\value)",
        r"Test loss: (?P<test_loss>\value)",
        r"Test accuracy: (?P<test_accuracy>\value)",  #
        *summary.DEFAULT_OUTPUT_SCALARS
    ]

    @staticmethod
    def test(script):
        return (
            _has_imports(script, [r"keras\.?", r"tensorflow\.?"])
            and _has_call(script, ["fit", "predict"])
        )


FRAMEWORKS = [Keras]


def _has_imports(script, patterns):
    return any(any(re.match(p, name) for p in patterns) for name in script.imports)


def _has_call(script, calls):
    return any(call.name in calls for call in script.calls)


class PythonFrameworkModelProxy(PythonScriptModelProxy):

    def __init__(self, script_path, framework):
        super().__init__(script_path, output_scalars=framework.output_scalars)
        self.framework = framework.name


class PythonFrameworksPlugin(pluginlib.Plugin, PythonScriptOpdefSupport):
    resolve_model_op_priority = 50

    def resolve_model_op(self, opspec):
        """Provide model op when running framework scripts directly."""

        model = model_for_script(opspec)
        if not model:
            return None
        self.log.debug("%s is a %s framework operation", opspec, model.framework)
        return model, model.op_name

    def python_script_opdef_loaded(self, opdef):
        """Apply framework output scalars to opdef main modules."""

        if opdef.output_scalars is not None:
            return

        script = _python_script_for_opdef_main(opdef)
        if not script:
            return

        framework = _framework_for_script(script)
        if not framework:
            return

        self.log.debug(
            "applying %s framework output scalars to %s", framework.name, opdef
        )
        opdef.output_scalars = framework.output_scalars


def model_for_script(script_path):
    script = _python_script_for_opspec(script_path)
    if not script:
        return None
    framework = _framework_for_script(script)
    if not framework:
        return None
    return PythonFrameworkModelProxy(script.src, framework)


def _python_script_for_opspec(opspec):
    path = os.path.join(config.cwd(), opspec)
    if not python_util.is_python_script(path):
        return None
    try:
        return python_util.Script(path)
    except SyntaxError:
        return None


def _framework_for_script(script):
    for f in FRAMEWORKS:
        if f.test(script):
            return f
    return None


def _python_script_for_opdef_main(opdef):
    assert opdef.main, opdef
    main_mod = op_util.split_cmd(opdef.main)[0]
    model_paths = op_util.opdef_model_paths(opdef)
    try:
        _path, mod_path = python_util.find_module(main_mod, model_paths)
    except ImportError:
        return None
    try:
        return python_util.Script(mod_path)
    except SyntaxError:
        return None

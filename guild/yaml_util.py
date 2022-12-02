# Copyright 2017-2022 RStudio, PBC
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

import yaml


def encode_yaml(val, default_flow_style=False):
    encoded = yaml.safe_dump(val, default_flow_style=default_flow_style, indent=2)
    return _strip_encoded_yaml(encoded)


def _strip_encoded_yaml(encoded):
    stripped = encoded.strip()
    if stripped.endswith("\n..."):
        stripped = stripped[:-4]
    return stripped


def decode_yaml(s):
    try:
        return yaml.safe_load(s)
    except yaml.scanner.ScannerError as e:
        raise ValueError(e) from e


def yaml_front_matter(filename):
    fm_s = _yaml_front_matter_s(filename)
    if not fm_s:
        return {}
    return yaml.safe_load(fm_s)


def _yaml_front_matter_s(filename):
    lines = []
    reading = False
    with open(filename) as f:
        for line in f:
            trimmed = line.rstrip()
            if not trimmed.lstrip():
                continue
            if trimmed == "---":
                if reading:
                    break
                reading = True
            elif reading:
                lines.append(trimmed)
            else:
                break
    return "\n".join(lines) if lines else None


def patch_yaml():
    patch_yaml_resolver()
    patch_yaml_bool_vals()


def patch_yaml_resolver():
    """Patch yaml parsing to support Guild specific resolution rules.

    - Make '+' or '-' optional in scientific notation
    - Make use of decimal '.' optional in scientific notation

    This patch replaces the default 'tag:yaml.org,2002:float' resolver
    with an augmented set of regex patterns. Refer to
    `yaml/resolver.py` for the original patterns.
    """
    yaml.resolver.Resolver.add_implicit_resolver(
        "tag:yaml.org,2002:float",
        # The patterns below are modified from the original set in two
        # ways: the first pattern makes `[-+]` optional and the second
        # pattern is a new pattern to match scientific notation that
        # does not include a decimal (e.g. `1e2`).
        re.compile(
            r"""^(?:[-+]?(?:[0-9][0-9_]*)\.[0-9_]*(?:[eE][-+]?[0-9]+)?
                    |[-+]?(?:[0-9][0-9_]*)(?:[eE][-+]?[0-9]+)
                    |\.[0-9_]+(?:[eE][-+][0-9]+)?
                    |[-+]?[0-9][0-9_]*(?::[0-5]?[0-9])+\.[0-9_]*
                    |[-+]?\.(?:inf|Inf|INF)
                    |\.(?:nan|NaN|NAN))$""",
            re.X,
        ),
        list("-+0123456789."),
    )


def patch_yaml_bool_vals():
    """Extends bool values to include single char variants.

    The YAML spec calls for bool values to support single char
    variants 'y', 'Y', 'n', and 'N'.

    The use of `bool_values` assumes `CANDIDATE.lower()` as input.
    """
    from yaml.constructor import SafeConstructor
    from yaml.resolver import Resolver

    SafeConstructor.bool_values = {
        "yes": True,
        "no": False,
        "true": True,
        "false": False,
        "on": True,
        "off": False,
        "y": True,
        "n": False,
    }

    Resolver.add_implicit_resolver(
        'tag:yaml.org,2002:bool', re.compile(r"^(?:y|Y|n|N)$", re.X), list("yYnN")
    )


if os.getenv("NO_PATCH_YAML") != "1":
    patch_yaml()

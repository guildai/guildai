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


def encode_yaml(val, default_flow_style=False, strict=False):
    """Returns val encoded as YAML.

    Uses PyYAML `safe_dump` to serialize `val`. `default_flow_style`
    is passed through to `safe_dump`.

    `strict` patches PyYAML to comply with the YAML standard code for
    single characters 'y' and 'n', which need to be quote to retain
    their string type as strict YAML. This is for compatibility
    outside PyYAML.
    """
    with StrictPatch(strict):
        encoded = yaml.safe_dump(
            val,
            default_flow_style=default_flow_style,
            indent=2,
        )
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


class StrictPatch:
    """Patches `yaml` to strictly adhere to the YAML spec*.

    Maybe used as a no-op with `StrictPatch(False)`.

    * This patch makes no guarantee of strict correctness but rather
      fixes known issues with PyYAML:

      - Encoding/decoding of single char boolean chars `[yYnN]`

    """

    implicit_resolver_patches = [
        (
            "tag:yaml.org,2002:bool",
            re.compile(r"^(?:y|Y|n|N)$", re.X),
            list('yYnN'),
        )
    ]

    bool_value_patches = {
        "y": True,
        "n": False,
    }

    def __init__(self, strict=True):
        self.strict = strict

    def __enter__(self):
        if not self.strict:
            return
        self._apply_implicit_resolver_patches()
        self._apply_bool_value_patches()

    def _apply_implicit_resolver_patches(self):
        for tag, pattern, first in self.implicit_resolver_patches:
            yaml.resolver.Resolver.add_implicit_resolver(tag, pattern, first)

    def _apply_bool_value_patches(self):
        for key, val in self.bool_value_patches.items():
            assert key not in yaml.constructor.SafeConstructor.bool_values, key
            yaml.constructor.SafeConstructor.bool_values[key] = val

    def __exit__(self, *_exc):
        if not self.strict:
            return
        self._unapply_implicit_resolver_patches()
        self._unapply_bool_value_patches()

    def _unapply_implicit_resolver_patches(self):
        for tag, pattern, first in self.implicit_resolver_patches:
            for ch in first:
                resolvers = yaml.resolver.Resolver.yaml_implicit_resolvers.get(ch)
                assert resolvers
                assert resolvers[-1] == (tag, pattern), (resolvers, tag, pattern)
                resolvers.pop()

    def _unapply_bool_value_patches(self):
        for key in self.bool_value_patches:
            del yaml.constructor.SafeConstructor.bool_values[key]


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
        # is a new pattern to match scientific notation that
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


if os.getenv("NO_PATCH_YAML") != "1":
    patch_yaml_resolver()

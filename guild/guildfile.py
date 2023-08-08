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

"""Provides support for the Guild file.

Design notes:

There are aspects to the Guild file that are language or plugin
specific -- e.g. `main`, `notebook`, and arguably `steps` operation
attributes. These features highlight a need to add Guild file parsing
logic to plugins. This exists to some extent already, via the plugin
`guildfile_data()`, `guildfile_loaded()`, and
`resolve_model_op()`. This API may be sufficient to correctly decouple
non-core features from the core and move them into plugins. For the
time being, such features are either encoded in the core or are
supported through an uncomfortable coupling between the core and
plugins (e.g. the Python script plugin is required to configure
`PYTHONPATH` when `main` and `steps` attributes are specified for an
operation).
"""

import copy
import logging
import os
import re
import sys

import yaml

from guild import config
from guild import opref
from guild import resourcedef
from guild import util

log = logging.getLogger("guild")

NAME = "guild.yml"

ALL_TYPES = [
    "config",
    "include",
    "model",
    "package",
]

MODEL_TYPES = ["model", "config"]

STRING_SRC_P = re.compile(r"<.*>$")
INCLUDE_REF_P1 = re.compile(r"([^:#]*):([^#]+)(?:#(.+))?")
INCLUDE_REF_P2 = re.compile(r"([^:#]+)(?:#(.+))?")
INCLUDE_REF_P_DESC = "CONFIG[#ATTRS] or MODEL:OPERATION[#ATTRS]"
PARAM_P = re.compile(r"({{.*?}})")

DEFAULT_PKG_VERSION = "0.0.0"

_cache = {}

###################################################################
# Exceptions
###################################################################


class GuildfileError(Exception):
    def __init__(self, guildfile_or_path, msg):
        super().__init__(guildfile_or_path, msg)
        if isinstance(guildfile_or_path, Guildfile):
            self.path = guildfile_or_path.src
        else:
            self.path = guildfile_or_path
        self.msg = msg

    def __str__(self):
        return f"error in {self.path or '<generated>'}: {self.msg}"


class NoModels(GuildfileError):
    def __init__(self, guildfile_or_path):
        super().__init__(guildfile_or_path, "no models")

    def __str__(self):
        return f"no models in {self.path}"


class GuildfileReferenceError(GuildfileError):
    pass


class GuildfileCycleError(GuildfileError):
    def __init__(self, guildfile_or_path, desc, cycle):
        msg = f"{desc} ({' -> '.join(cycle)})"
        super().__init__(guildfile_or_path, msg)


class GuildfileIncludeError(GuildfileError):
    def __init__(self, guildfile_or_path, include):
        msg = (
            f"cannot find include '{include}' "
            "(includes must be local to including Guild file or a "
            "Guild package on the system path)"
        )
        super().__init__(guildfile_or_path, msg)


class GuildfileMissing(Exception):
    pass


###################################################################
# Helpers
###################################################################


def _required(name, data, guildfile, pop=False):
    try:
        if pop:
            return data.pop(name)
        return data[name]
    except KeyError:
        raise GuildfileError(
            guildfile, f"missing required '{name}' attribute in {data!r}"
        ) from None


def _string_source(src):
    return STRING_SRC_P.match(src)


###################################################################
# Guildfile
###################################################################


class Guildfile:
    def __init__(
        self,
        data,
        src=None,
        dir=None,
        included=None,
        extends_seen=None,
    ):
        if not dir and src and not _string_source(src):
            dir = os.path.dirname(src)
        if src is None and dir is None:
            raise ValueError("either src or dir must be specified")
        self.src = src
        self.dir = dir
        self.models = {}
        self.package = None
        coerced = _coerce_guildfile_data(data, self)
        self.data = self._expand_data_includes(coerced, included or [])
        try:
            self._apply_data(extends_seen or [])
        except (GuildfileError, resourcedef.ResourceFormatError):
            raise
        except Exception as e:
            log.error("loading %s: %r", self.src, e)
            raise

    def _expand_data_includes(self, data, included):
        i = 0
        while i < len(data):
            item = data[i]
            try:
                includes = item["include"]
            except KeyError:
                i += 1
            else:
                new_items = self._include_data(includes, included)
                data[i:i + 1] = new_items
                i += len(new_items)
        return data

    def _include_data(self, includes, included):
        if self.src and not _string_source(self.src):
            included.append(os.path.abspath(self.src))
        include_data = []
        for path in includes:
            path = self._find_include(path)
            if path in included:
                raise GuildfileCycleError(
                    "cycle in 'includes'", included[0], included + [path]
                )
            data = yaml.safe_load(open(path, "r"))
            guildfile = Guildfile(data, path, included=included)
            include_data.extend(guildfile.data)
        return include_data

    def _find_include(self, include):
        path = util.find_apply(
            [self._local_include, self._sys_path_include, self._gpkg_include], include
        )
        if path:
            return path
        raise GuildfileIncludeError(self, include)

    def _local_include(self, path):
        log.debug("looking for include '%s' in %s", path, self.dir)
        full_path = os.path.abspath(os.path.join(self.dir or "", path))
        if os.path.exists(full_path):
            log.debug("found include %s", full_path)
            return full_path
        return None

    @staticmethod
    def _sys_path_include(include):
        include_path = include.replace(".", os.path.sep)
        for path in sys.path:
            log.debug("looking for include '%s' in %s", include, path)
            guildfile = guildfile_path(path, include_path)
            if os.path.exists(guildfile):
                log.debug("found include %s", guildfile)
                return guildfile
        return None

    def _gpkg_include(self, include):
        return self._sys_path_include("gpkg." + include)

    def _apply_data(self, extends_seen):
        for item in self.data:
            item_type, name = self._validated_item_type(item)
            if item_type == "model":
                self._apply_model(name, item, extends_seen)
            elif item_type == "package":
                self._apply_package(name, item)

    def _validated_item_type(self, item):
        used = [name for name in ALL_TYPES if name in item]
        if not used:
            raise GuildfileError(
                self,
                f"missing required type (one of: {', '.join(ALL_TYPES)}) in {item!r}",
            )
        if len(used) > 1:
            raise GuildfileError(
                self, f"multiple types ({', '.join(used)}) in {item!r}"
            )
        validated_type = used[0]
        name = item[validated_type]
        if not isinstance(name, str):
            raise GuildfileError(
                self, f"invalid {validated_type} name ${name!r}: expected a string"
            )
        return validated_type, name

    def _apply_model(self, name, data, extends_seen):
        if name in self.models:
            raise GuildfileError(self, f"duplicate model '{name}'")
        model = ModelDef(name, data, self, extends_seen)
        self.models[name] = model

    def _apply_package(self, name, data):
        if self.package:
            raise GuildfileError(self, "mutiple package definitions")
        self.package = PackageDef(name, data, self)

    @property
    def default_model(self):
        models = list(self.models.values())
        if len(models) == 1:
            return models[0]
        for m in models:
            if m.default:
                return m
        return None

    @property
    def default_operation(self):
        model = self.default_model
        if not model:
            return None
        return model.default_operation

    def __repr__(self):
        return f"<guild.guildfile.Guildfile '{self}'>"

    def __str__(self):
        return self.src or self.dir

    def __eq__(self, _x):
        raise AssertionError()


###################################################################
# Coercion rules
###################################################################


def _coerce_guildfile_data(data, guildfile):
    if data is None:
        return []
    if isinstance(data, dict):
        data = [_anonymous_model_data(data)]
    if not isinstance(data, list):
        raise GuildfileError(
            guildfile, f"invalid guildfile data {data!r}: expected a mapping"
        )
    return [_coerce_guildfile_item_data(item_data, guildfile) for item_data in data]


def _anonymous_model_data(ops_data):
    """Returns a dict representing an anonymous model.

    ops_data must be a dict representing the model operations. It will
    be used unmodified for the model `operations` attribute.
    """
    return {"model": "", "operations": ops_data}


def _coerce_guildfile_item_data(data, guildfile):
    """Coerces top-level object attributes based on name.

    Refer to _coerce_top_level_attr for coerced attributes.
    """
    if not isinstance(data, dict):
        return data
    coerced = {
        name: _coerce_top_level_attr(name, val, guildfile)
        for name, val in data.items()
    }
    _maybe_apply_anonymous_model(coerced)
    return coerced


def _coerce_top_level_attr(name, val, guildfile):
    """Coerces top-level object attributes by name.

    This function is unaware of context so an attribute "flags" under
    an operation is coerced using the same rules as a "flags"
    attribute under "config". This scheme relies on common rules
    applied to object attributes with the same name. This is not
    necessarily the case (e.g. "flags" for a step defines values, not
    flag defs) and so is a limitation of this approach.
    """
    if name == "include":
        return _coerce_include(val, guildfile)
    if name == "extends":
        return _coerce_extends(val, guildfile)
    if name == "operations":
        return _coerce_operations(val, guildfile)
    if name == "flags":
        return _coerce_flags(val, guildfile)
    if name == "sourcecode":
        return _coerce_select_files(val, guildfile)
    return val


def _coerce_include(data, guildfile):
    return _coerce_str_to_list(data, guildfile, "include")


def _coerce_extends(data, guildfile):
    return _coerce_str_to_list(data, guildfile, "extends")


def _coerce_operations(data, guildfile):
    if not isinstance(data, dict):
        raise GuildfileError(
            guildfile, f"invalid operations value {data!r}: expected a mapping"
        )
    return {
        op_name: _coerce_operation(op_name, op, guildfile)
        for op_name, op in data.items()
    }


def _coerce_operation(name, data, guildfile):
    if name == "$include":
        return data
    if isinstance(data, str):
        return {"main": data}
    if isinstance(data, dict):
        return {
            name: _coerce_operation_attr(name, val, guildfile)
            for name, val in data.items()
        }
    raise GuildfileError(
        guildfile,
        f"invalid value for operation '{data}' {name!r}: expected a string or a mapping",
    )


def _coerce_operation_attr(name, val, guildfile):
    if name == "flags":
        return _coerce_flags(val, guildfile)
    if name == "flags-import":
        return _coerce_flags_import(val, guildfile)
    if name == "publish":
        return _coerce_publish(val, guildfile)
    if name == "python-path":
        return _coerce_op_python_path(val, guildfile)
    if name == "output-scalars":
        return _coerce_output_capture(val, guildfile, "output-scalars")
    if name == "output-attrs":
        return _coerce_output_capture(val, guildfile, "output-attrs")
    if name == "sourcecode":
        return _coerce_select_files(val, guildfile)
    return val


def _coerce_flags(data, guildfile):
    if not isinstance(data, dict):
        raise GuildfileError(
            guildfile, f"invalid flags value {data!r}: expected a mapping"
        )
    return {name: coerce_flag_data(name, val, guildfile) for name, val in data.items()}


def coerce_flag_data(name, data, guildfile):
    if name == "$include":
        return str(data)
    if isinstance(data, dict):
        return data
    if isinstance(data, (str, int, float, bool, list)):
        return {"default": data}
    if data is None:
        return {"default": None}
    raise GuildfileError(
        guildfile,
        f"invalid value for {name} flag {data!r}: expected a mapping of "
        "flag attributes or default flag value",
    )


def _coerce_flags_import(data, guildfile):
    if data in (True, "all"):
        return True
    if data is False:
        return []
    if isinstance(data, list):
        return data
    raise GuildfileError(
        guildfile,
        f"invalid flags-import value {data!r}: expected yes/all, "
        "no, or a list of flag names",
    )


def _coerce_op_python_path(data, guildfile):
    if data is None:
        return None
    return _coerce_str_to_list(data, guildfile, "python-path")


def _coerce_output_capture(data, guildfile, attr_name):
    if data is None:
        return None
    if data is False:
        return []
    if isinstance(data, str):
        return [data]
    if isinstance(data, dict):
        return [data]
    if isinstance(data, list):
        return data
    raise GuildfileError(
        guildfile,
        f"invalid {attr_name} {data!r}: expected a mapping, list, string, or false",
    )


def _coerce_publish(data, guildfile):
    files = data.get("files")
    if files:
        data = dict(data)
        data["files"] = _coerce_select_files(files, guildfile)
    return data


def _coerce_select_files(data, guildfile):
    if data is None:
        return _coerce_select_files_default()
    if data is False or data == []:
        return _coerce_select_files_disabled()
    if isinstance(data, str):
        return _coerce_select_files_one_include(data)
    if isinstance(data, dict):
        return _coerce_select_files_dict(data, guildfile)
    if isinstance(data, list):
        return _coerce_select_files_list(data, guildfile)
    raise GuildfileError(
        guildfile,
        f"invalid select files spec {data!r}: expected a string, list, or mapping",
    )


def _coerce_select_files_default():
    # By default, no select criteria
    return []


def _coerce_select_files_disabled():
    return False


def _coerce_select_files_one_include(data):
    return [{"exclude": "*"}, {"include": data}]


def _coerce_select_files_dict(data: dict, guildfile):
    assert isinstance(data, dict)
    data = dict(data)  # used for pop/validation
    coerced = {
        "select": _coerce_select_files(data.pop("select", None), guildfile),
        "root": data.pop("root", None),
        "digest": data.pop("digest", None),
        "dest": data.pop("dest", None),
    }
    if data:
        guildfile_path = os.path.relpath(guildfile.src or guildfile.dir or "")
        log.warning(
            "unexpected sourcecode attribute(s) in %s: %s",
            guildfile_path,
            ", ".join(sorted(data)),
        )
    return coerced


def _coerce_select_files_list(data, guildfile):
    assert isinstance(data, list), data
    all_strings = True
    items = []
    for item in data:
        if isinstance(item, str):
            items.append({"include": item})
        elif isinstance(item, dict):
            items.append(item)
            all_strings = False
        else:
            raise GuildfileError(
                guildfile, f"invalid sourcecode {item!r}: expected a string or mapping"
            )
    if all_strings:
        items.insert(0, {"exclude": "*"})
    return items


def _coerce_str_to_list(val, guildfile, name):
    if isinstance(val, str):
        if val.startswith("[") and val.endswith("]"):
            val = yaml.safe_load(val)
        else:
            val = [val]
    elif isinstance(val, list):
        pass
    elif val is None:
        val = []
    else:
        raise GuildfileError(
            guildfile, f"invalid {name} value {val!r}: expected a string or list"
        )
    # type hint for type checking, or else the eval above is ambiguous
    assert isinstance(val, list)
    return val


###################################################################
# Include attribute support
###################################################################


def _resolve_includes(data, section_name, guildfiles):
    assert isinstance(data, dict), data
    resolved = {}
    seen_includes = set()
    section_data = data.get(section_name) or {}
    _apply_section_data(section_data, guildfiles, section_name, seen_includes, resolved)
    return resolved


def _apply_section_data(data, guildfile_path, section_name, seen_includes, resolved):
    for name in _includes_first(data):
        if name == "$include":
            includes = _coerce_includes(data[name], guildfile_path[0])
            _apply_includes(
                includes, guildfile_path, section_name, seen_includes, resolved
            )
        else:
            _apply_data(name, data[name], resolved)


def _includes_first(names):
    return sorted(names, key=lambda x: "\x00" if x == "$include" else x)


def _coerce_includes(val, src):
    return _coerce_str_to_list(val, src, "$include")


def _apply_includes(includes, guildfile_path, section_name, seen_includes, resolved):
    _assert_guildfile_data(guildfile_path[0])
    for ref in includes:
        if ref in seen_includes:
            break
        seen_includes.add(ref)
        # Have to access guildfile.data here rather than use
        # guildfile.get because guildfile may not be initialized at
        # this point.
        include_model, include_op, include_attrs = _split_include_ref(
            ref, guildfile_path[0]
        )
        include_data = _find_include_data(
            include_model, include_op, section_name, guildfile_path
        )
        if include_data is None:
            raise GuildfileReferenceError(
                guildfile_path[0],
                f"invalid include reference '{ref}': cannot find target",
            )
        if include_attrs:
            include_data = _filter_data(include_data, include_attrs)
        _apply_section_data(
            include_data, guildfile_path, section_name, seen_includes, resolved
        )


def _assert_guildfile_data(guildfile):
    # This is called by guildfile components that need to access
    # guildfile data before the modefile is fully initialized.
    assert hasattr(guildfile, "data"), "modesfile data not initialized"


def _split_include_ref(ref, src):
    m = INCLUDE_REF_P1.match(ref)
    if m:
        groups = m.groups()
        assert len(groups) == 3, (groups, ref)
        return groups
    m = INCLUDE_REF_P2.match(ref)
    if m:
        groups = m.groups()
        assert len(groups) == 2, (groups, ref)
        return groups[0], None, groups[1]
    raise GuildfileReferenceError(
        src,
        (
            f"invalid include reference '{ref}': operation references "
            f"must be specified as {INCLUDE_REF_P_DESC}"
        ),
    )


def _find_include_data(
    model_name,
    op_name,
    section_name,
    guildfile_path,
):
    for guildfile in guildfile_path:
        for top_level_data in guildfile.data:
            if _item_name(top_level_data, MODEL_TYPES) == model_name:
                if op_name:
                    op_data = _op_data(top_level_data, op_name)
                    if op_data is None:
                        continue
                    return op_data.get(section_name) or {}
                return top_level_data.get(section_name) or {}
    return None


def _item_name(data, types):
    for attr in types:
        try:
            return data[attr]
        except KeyError:
            pass
    return None


def _op_data(model_data, op_name):
    return model_data.get("operations", {}).get(op_name)


def _filter_data(data, attrs):
    return {name: data[name] for name in data if name in attrs}


def _apply_data(name, data, resolved):
    if isinstance(data, dict):
        # Safe to merge data items into resolved
        try:
            cur = resolved[name]
        except KeyError:
            new = {}
            new.update(data)
            resolved[name] = new
        else:
            _apply_missing_vals(cur, data)
    else:
        # Non-dict data applied to resolved as-is
        resolved[name] = data


def _apply_missing_vals(target, source):
    for name in source:
        target[name] = source[name]


###################################################################
# Model def
###################################################################


class ModelDef:
    def __init__(self, name, data, guildfile, extends_seen=None):
        data = _extended_data(data, guildfile, extends_seen or [])
        self.guildfile = guildfile
        self.name = name
        self.op_default_config = _init_op_default_config(data, guildfile)
        self.default = bool(data.get("default"))
        self.parents = _dedup_parents(data.get("__parents__", []))
        self.description = (data.get("description") or "").strip()
        self.references = data.get("references") or []
        self.operations = _init_ops(data, self)
        self.resources = _init_resources(data, self)
        self.plugins = _init_plugins(data.get("plugins"), guildfile)
        self.extra = data.get("extra") or {}
        self.sourcecode = _init_sourcecode(data.get("sourcecode"), guildfile)
        self.python_requires = data.get("python-requires")

    @property
    def guildfile_search_path(self):
        return [self.guildfile] + self.parents

    def __repr__(self):
        return f"<guild.guildfile.ModelDef '{self.name}'>"

    def __getitem__(self, name):
        if name is None:
            raise ValueError("name cannot be None")
        for op in self.operations:
            if op.name == name:
                return op
        raise KeyError(name)

    def __eq__(self, other):
        if other:
            return self.name == other.name
        return False

    def get_operation(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    @property
    def default_operation(self):
        public_ops = []
        for op in self.operations:
            if op.default:
                return op
            if op.name[:1] != "_":
                public_ops.append(op)
        if len(public_ops) == 1:
            return public_ops[0]
        return None

    def get_resource(self, name, default=None):
        for res in self.resources:
            if res.name == name:
                return res
        return default


def _extended_data(config_data, guildfile, seen=None, resolve_params=True):
    data = copy.deepcopy(config_data)
    extends = config_data.get("extends") or []
    if extends:
        _apply_parents_data(extends, guildfile, seen, data)
    if resolve_params:
        data = _resolve_param_refs(data, _params(data))
    return data


def _params(data):
    params = data.get("params") or {}
    return {name: _resolve_param(name, params) for name in params}


def _resolve_param(name, params):
    val = params[name]
    if not isinstance(val, str):
        return val
    iter_count = 0
    seen = set()
    seen.add(val)
    # Resolve val until we get a value that we've already seen (either
    # fully resolved or a cycle). Use iter counter to guard against
    # non-terminating loops.
    while iter_count < 100:
        val = _resolve_str_param_refs(val, params)
        if val in seen:
            return val
        seen.add(val)
        iter_count += 1
    assert False, (name, params)


def _apply_parents_data(extends, guildfile, seen, data):
    for name in extends:
        if name in seen:
            raise GuildfileCycleError(guildfile, "cycle in 'extends'", seen + [name])
        parent = _parent_data(name, guildfile, seen)
        inheritable = [
            "description",
            "extra",
            "flags",
            "operation-defaults",
            "operations",
            "params",
            "references",
            "resources",
            "sourcecode",
        ]
        _apply_parent_pkg_guildfile(parent, data)
        _apply_parent_data(parent, data, inheritable)


def _parent_data(name, guildfile, seen):
    if "/" in name:
        return _pkg_parent_data(name, guildfile, seen)
    return _guildfile_parent_data(name, guildfile, seen)


def _pkg_parent_data(name, guildfile, seen):
    pkg, model_name = name.split("/", 1)
    if not model_name:
        raise GuildfileReferenceError(
            guildfile,
            f"invalid model or config reference '{name}': missing model name",
        )
    pkg_guildfile_path = _find_pkg_guildfile(pkg)
    if not pkg_guildfile_path:
        raise GuildfileReferenceError(
            guildfile, f"cannot find Guild file for package '{pkg}'"
        )
    pkg_guildfile = for_file(pkg_guildfile_path, seen + [name])
    parent_data = _modeldef_data(model_name, pkg_guildfile)
    if parent_data is None:
        raise GuildfileReferenceError(
            guildfile, f"undefined model or config '{model_name}' in package '{pkg}'"
        )
    parent_data["__pkg_guildfile__"] = pkg_guildfile
    return _extended_data(parent_data, pkg_guildfile, seen + [name], False)


def _modeldef_data(name, guildfile):
    for item in guildfile.data:
        if _item_name(item, MODEL_TYPES) == name:
            return item
    return None


def _find_pkg_guildfile(pkg):
    pkg_path = pkg.replace("-", "_").replace(".", os.path.sep)
    for path in sys.path:
        log.debug("looking for pkg '%s' in %s", pkg, path)
        guildfile = guildfile_path(path, pkg_path)
        if os.path.exists(guildfile):
            log.debug("found pkg Guild file %s", guildfile)
            return guildfile
    return None


def _guildfile_parent_data(name, guildfile, seen):
    parent_data = _modeldef_data(name, guildfile)
    if parent_data is None:
        raise GuildfileReferenceError(guildfile, f"undefined model or config '{name}'")
    return _extended_data(parent_data, guildfile, seen + [name], False)


def _apply_parent_pkg_guildfile(parent, child):
    parents = parent.get("__parents__", [])
    try:
        parent_pkg_guildfile = parent["__pkg_guildfile__"]
    except KeyError:
        pass
    else:
        parents.append(parent_pkg_guildfile)
    child.setdefault("__parents__", []).extend(parents)


def _apply_parent_data(parent, child, attrs=None):
    if not isinstance(parent, dict) or not isinstance(child, dict):
        return
    for name, parent_val in parent.items():
        if attrs is not None and name not in attrs:
            continue
        try:
            child_val = child[name]
        except KeyError:
            _apply_value(child, name, parent_val)
        else:
            _apply_parent_data(parent_val, child_val)


def _apply_value(target, name, val):
    target[name] = copy.deepcopy(val)


def _resolve_param_refs(val, params):
    if isinstance(val, dict):
        return _resolve_dict_param_refs(val, params)
    if isinstance(val, list):
        return _resolve_list_param_refs(val, params)
    if isinstance(val, str):
        return _resolve_str_param_refs(val, params)
    return val


def _resolve_dict_param_refs(d, params):
    return {name: _resolve_param_refs(val, params) for name, val in d.items()}


def _resolve_list_param_refs(l, params):
    return [_resolve_param_refs(x, params) for x in l]


def _resolve_str_param_refs(s, params):
    parts = [part for part in PARAM_P.split(str(s)) if part != ""]
    resolved = [_resolve_param_ref(part, params) for part in parts]
    if len(resolved) == 1:
        return resolved[0]
    return "".join([str(part) for part in resolved])


def _resolve_param_ref(val, params):
    if val.startswith("{{") and val.endswith("}}"):
        ref_name = val[2:-2].strip()
    else:
        return val
    try:
        return params[ref_name]
    except KeyError:
        return val


def _init_op_default_config(data, guildfile):
    config = data.get("operation-defaults")
    if not config:
        return {}
    return _coerce_operation("operation-defaults", config, guildfile)


def _dedup_parents(parents):
    seen = set()
    deduped = []
    for parent in parents:
        if parent.dir in seen:
            continue
        deduped.append(parent)
        seen.add(parent.dir)
    return deduped


def _init_ops(data, modeldef):
    ops_data = _resolve_includes(data, "operations", modeldef.guildfile_search_path)
    return [OpDef(key, ops_data[key], modeldef) for key in sorted(ops_data)]


def _init_resources(data, modeldef):
    data = _resolve_includes(data, "resources", modeldef.guildfile_search_path)
    return [ResourceDef(key, data[key], modeldef) for key in sorted(data)]


def _init_plugins(data, guildfile):
    if data is None or data is True:
        return None
    if data is False:
        return []
    return _coerce_str_to_list(data, guildfile, "plugins")


def _init_sourcecode(data, guildfile):
    return FileSelectDef(data, guildfile)


###################################################################
# Op def
###################################################################


class OpDef:
    def __init__(self, name, data, modeldef):
        if not isinstance(data, dict):
            raise GuildfileError(
                modeldef.guildfile,
                f"invalid operation def {data!r}: expected a mapping",
            )
        if not isinstance(name, str):
            raise GuildfileError(
                modeldef.guildfile,
                f"invalid operation name {name!r}: expected a string",
            )
        _apply_op_default_config(modeldef, data)
        self.name = name
        self._data = data
        self.modeldef = modeldef
        self.guildfile = modeldef.guildfile
        self.default = bool(data.get("default"))
        self.flags = _init_flags(data, self)
        self.flags_dest = data.get("flags-dest")
        self.flags_import = data.get("flags-import")
        self.flags_import_skip = data.get("flags-import-skip")
        self._modelref = None
        # TODO - remove _flag_vals support once op2 is promoted
        self._flag_vals = _init_flag_values(self.flags)
        self.description = (data.get("description") or "").strip()
        self.exec_ = data.get("exec")
        self.main = _init_op_main(data)
        self.steps = _steps_data(data, self)
        self.python_requires = data.get("python-requires")
        self.python_path = data.get("python-path")
        self.env = data.get("env") or {}
        self.env_secrets = data.get("env-secrets")
        self.plugins = _init_plugins(data.get("plugins"), self.guildfile)
        self.dependencies = _init_dependencies(data.get("requires"), self)
        self.stoppable = data.get("stoppable") or False
        self.label = data.get("label")
        self.tags = _coerce_str_to_list(data.get("tags"), self.guildfile, "tags")
        self.compare = data.get("compare")
        self.handle_keyboard_interrupt = data.get("handle-keyboard-interrupt") or False
        self.flag_encoder = data.get("flag-encoder")
        self.default_max_trials = data.get("default-max-trials")
        self.output_scalars = data.get("output-scalars")
        self.output_attrs = data.get("output-attrs")
        self.objective = data.get("objective")
        self.optimizers = _init_optimizers(data, self)
        self.publish = _init_publish(data.get("publish"), self)
        self.sourcecode = _init_sourcecode(data.get("sourcecode"), self.guildfile)
        self.default_flag_arg_skip = data.get("default-flag-arg-skip") or False
        self.pip_freeze = data.get("pip-freeze")
        self.delete_on_success = data.get("delete-on-success") or False
        self.can_stage_trials = data.get("can-stage-trials") or False
        self.run_attrs = data.get("run-attrs")

    def __repr__(self):
        return f"<guild.guildfile.OpDef '{self.fullname}'>"

    def __eq__(self, other):
        if other:
            return self.name == other.name
        return False

    def as_data(self):
        return self._data

    @property
    def fullname(self):
        if self.modeldef and self.modeldef.name:
            return f"{self.modeldef.name}:{self.name}"
        return self.name

    def set_modelref(self, modelref):
        self._modelref = modelref

    @property
    def opref(self):
        if not self._modelref:
            raise ValueError('set_modelref() must be called before reading opref')
        return opref.OpRef.for_op(self.name, self._modelref)

    def get_flagdef(self, name):
        for flag in self.flags or []:
            if flag.name == name:
                return flag
        return None

    def flag_values(self, include_none=True):
        return dict(self._iter_flag_values(include_none))

    def _iter_flag_values(self, include_none):
        for name, val in self._flag_vals.items():
            if val is not None or include_none:
                yield name, val

    # TODO: remove this - it's a hack - Guildfile should be immutable
    def set_flag_value(self, name, val):
        self._flag_vals[name] = val

    def get_flag_value(self, name, default=None):
        try:
            return self._flag_vals[name]
        except KeyError:
            return default

    def merge_flags(self, opdef):
        """Merges flags defined in opdef into self

        Self values take precedence over opdef values.
        """
        merged = {}
        for op_flag in opdef.flags:
            self_flag = self._mergeable_flagdef(op_flag.name)
            if self_flag is None:
                merged[op_flag.name] = _new_merged_flag(op_flag, self)
            else:
                merged[self_flag.name] = self_flag
                _apply_flag_attrs(op_flag, self_flag)
        for self_flag in self.flags or []:
            if self_flag.name not in merged:
                merged[self_flag.name] = self_flag
        self.flags = [merged[name] for name in sorted(merged)]
        self._flag_vals = _init_flag_values(self.flags)

    def _mergeable_flagdef(self, name):
        """Returns flagdef that can be merge per name.

        Considers flag arg_name if name cannot be found.
        """
        by_name = self.get_flagdef(name)
        if by_name is not None:
            return by_name
        for flag in self.flags or []:
            if flag.arg_name and flag.arg_name == name:
                return flag
        return None

    def get_optimizer(self, name):
        for opt in self.optimizers or []:
            if opt.name == name:
                return opt
        return None

    @property
    def default_optimizer(self):
        return _default_optimizer(self.optimizers)


def _default_optimizer(optimizers):
    if len(optimizers) == 1:
        return optimizers[0]
    for opt in optimizers or []:
        if opt.default:
            return opt
    return None


def _apply_op_default_config(modeldef, data):
    config = modeldef.op_default_config
    if not config or not isinstance(config, dict):
        return
    for key in config:
        if key not in data:
            data[key] = copy.copy(config[key])


def _init_flags(data, opdef):
    data = _resolve_includes(data, "flags", opdef.modeldef.guildfile_search_path)
    return [FlagDef(name, data[name], opdef) for name in sorted(data)]


def _new_merged_flag(src_flag, opdef):
    new_flag = copy.deepcopy(src_flag)
    new_flag.opdef = opdef
    return new_flag


def _apply_flag_attrs(src_flag, dest_flag):
    # Use a baseline flag def to get default values for empty data.
    baseline_flag = FlagDef("", {}, None)
    for name in dir(src_flag):
        if name[:1] == "_":
            continue
        dest_val = getattr(dest_flag, name, None)
        baseline_val = getattr(baseline_flag, name, None)
        if dest_val == baseline_val:
            setattr(dest_flag, name, getattr(src_flag, name))


class FlagDef:
    def __init__(self, name, data, opdef):
        if not isinstance(data, dict):
            raise GuildfileError(
                opdef.guildfile, f"invalid flag data {data!r}: expected a mapping"
            )
        self.name = name
        self.opdef = opdef
        _data = dict(data)  # copy - used for pop
        self.default = _data.pop("default", None)
        self.description = _data.pop("description", None) or ""
        self.type = _data.pop("type", None)
        self.required = bool(_data.pop("required", False))
        self.alias = _data.pop("alias", None)
        self.arg_name = _data.pop("arg-name", None)
        self.arg_encoding = _data.pop("arg-encoding", None)
        self.arg_skip = _data.pop("arg-skip", None)
        self.arg_switch = _data.pop("arg-switch", None)
        self.arg_split = _data.pop("arg-split", None)
        self.choices = _init_flag_choices(_data.pop("choices", None), self)
        self.allow_other = _data.pop("allow-other", False)
        self.env_name = _data.pop("env-name", None)
        self.env_encoding = _data.pop("env-encoding", None)
        self.null_label = _data.pop("null-label", None)
        self.min = _data.pop("min", None)
        self.max = _data.pop("max", None)
        self.distribution = data.pop("distribution", None)
        self.extra = _data

    def __repr__(self):
        return f"<guild.guildfile.FlagDef '{self.name}'>"


def _init_flag_values(flagdefs):
    return {flag.name: flag.default for flag in flagdefs}


def _init_flag_choices(data, flagdef):
    if not data:
        return []
    if not isinstance(data, list):
        raise GuildfileError(
            flagdef.opdef.guildfile,
            f"invalid flag choice data {data!r}: expected a list of values or mappings",
        )
    return [FlagChoice(choice_data, flagdef) for choice_data in data]


class FlagChoice:
    def __init__(self, data, flagdef):
        self.flagdef = flagdef
        if isinstance(data, dict):
            self.value = _required("value", data, flagdef.opdef.guildfile)
            self.description = data.get("description") or ""
            self.flags = data.get("flags") or {}
            self.alias = data.get("alias")
        else:
            self.value = data
            self.description = ""
            self.flags = {}
            self.alias = None

    def __repr__(self):
        return f"<guild.guildfile.FlagChoice {self.value!r}>"


def _init_op_main(data):
    return data.get("main") or _maybe_nbexec_main(data)


def _maybe_nbexec_main(data):
    try:
        notebook = data["notebook"]
    except KeyError:
        return None
    else:
        return f"guild.plugins.nbexec {notebook}"


def _steps_data(data, opdef):
    """Return steps data for opdef data.

    Supports `$include` for flag mappings, where used.

    We don't parse steps data to a structure the way other data values
    are parsed by this module. Instead we pass data through to be
    saved in its raw format for `batch_main` to parse. This is
    less-than-ideal as we should validate the data before a workflow
    operation starts.

    This is an opportunistic implementation that purportedly saves
    development effort and reduces the double-effort of re-parsing the
    `steps` run attribute, which is used as the interface for stepped
    runs.
    """
    steps_data = data.get("steps")
    if not steps_data:
        return None
    if not isinstance(steps_data, list):
        raise GuildfileError(
            opdef.guildfile, f"invalid steps data {steps_data!r}: expected a list"
        )
    return [_step_data(step, opdef) for step in steps_data]


def _step_data(data, opdef):
    if not isinstance(data, dict):
        return data
    _apply_step_flags(data, opdef, data)
    return data


def _apply_step_flags(data, opdef, target):
    if not data:
        return
    flags_data = _resolve_includes(data, "flags", opdef.modeldef.guildfile_search_path)
    if flags_data:
        target["flags"] = _step_flag_values(flags_data)


def _step_flag_values(flags_data):
    return {key: _step_flag_value(val) for key, val in flags_data.items()}


def _step_flag_value(val):
    if isinstance(val, dict):
        return val.get("default")
    return val


def _init_dependencies(requires, opdef):
    if not requires:
        return []
    if not isinstance(requires, list):
        requires = [requires]
    return [OpDependencyDef(data, opdef) for data in requires]


class OpDependencyDef:
    spec = None
    description = None
    inline_resource = None

    def __init__(self, data, opdef):
        self.opdef = opdef
        self.modeldef = opdef.modeldef
        if isinstance(data, str):
            self.spec = data
            self.description = ""
        elif isinstance(data, dict):
            if "resource" in data:
                self.spec = data["resource"]
                self.description = data.get("description") or ""
            else:
                self.inline_resource = _init_inline_resource(data, opdef)
        else:
            raise GuildfileError(
                self,
                f"invalid dependency value {data!r}: expected a string or mapping",
            )
        # Op dependency must always be a spec or an inline resource.
        assert self.spec or self.inline_resource

    def __repr__(self):
        if self.inline_resource:
            return (
                "<guild.guildfile.OpDependencyDef "
                f"{self.inline_resource.resolving_name}>"
            )
        return f"<guild.guildfile.OpDependencyDef '{self.spec}'>"

    def __str__(self):
        return self.__repr__()

    @property
    def name(self):
        # See __init__ - op dep must be a spec or inline
        assert self.spec or self.inline_resource
        return self.spec or (self.inline_resource and self.inline_resource.name)


def _init_inline_resource(data, opdef):
    data = _coerce_inline_resource_data(data)
    res = ResourceDef(data.get("name"), data, opdef.modeldef)
    return res


def _coerce_inline_resource_data(data):
    if "sources" in data:
        return data
    # If sources not explicitly provided in data, assume data is a
    # source.
    return {"sources": [data]}


def _init_optimizers(data, opdef):
    opts_data = _coerce_opts_data(data, opdef)
    return [
        OptimizerDef(name, opt_data, opdef)
        for name, opt_data in sorted(opts_data.items())
    ]


def _coerce_opts_data(data, opdef):
    if "optimizer" in data and "optimizers" in data:
        raise GuildfileError(
            opdef.modeldef.guildfile,
            f"conflicting optimizer configuration in operation '{opdef.name}' "
            "- cannot define both 'optimizer' and 'optimizers'",
        )
    opts_data = util.find_apply(
        [
            lambda: data.get("optimizers"),
            lambda: _coerce_single_optimizer(data.get("optimizer"), opdef),
            lambda: {},
        ]
    )
    if isinstance(opts_data, list):
        opts_data = {name: {} for name in opts_data}
    elif isinstance(opts_data, dict):
        pass
    else:
        raise GuildfileError(
            opdef.modeldef.guildfile,
            f"invalid optimizer config {data!r}: expected list or mapping",
        )
    return {
        name: _coerce_opt_data_item(opt_data)
        for name, opt_data in opts_data.items()
    }


def _coerce_single_optimizer(data, opdef):
    if data is None:
        return None
    coerced = _coerce_opt_data_item(data)
    name = _required("algorithm", coerced, opdef.modeldef.guildfile)
    return {name: coerced}


def _coerce_opt_data_item(data):
    if isinstance(data, str):
        data = {"algorithm": data}
    return data


class OptimizerDef:
    def __init__(self, name, data, opdef):
        data = dict(data)
        self.name = name
        self.opdef = opdef
        # Internally an optimizer algorithm is an opspec but we
        # represent it to the user as an algorithm.
        self.opspec = data.pop("algorithm", None) or name
        self.default = data.pop("default", False)
        # Note that the rest of `data` is treated as optimizer
        # flags. This scheme prohibits the use of any of the above
        # keys (e.g. 'algorithm', 'default') as flag names.
        self.flags = data

    @classmethod
    def for_name(cls, name, opdef):
        return cls(name, {"algorithm": name}, opdef)

    def __repr__(self):
        return f"<guild.guildfile.OptimizerDef '{self.name}'>"

    def __str__(self):
        return self.__repr__()


class PublishDef:
    def __init__(self, data, opdef):
        self.opdef = opdef
        if data is None:
            data = {}
        self.files = FileSelectDef(data.get("files"), opdef.guildfile)
        self.template = data.get("template")


def _init_publish(data, opdef):
    return PublishDef(data, opdef)


###################################################################
# File select def
###################################################################


class FileSelectDef:
    def __init__(self, data, guildfile):
        if isinstance(data, dict):
            self._dict_init(data, guildfile)
        else:
            self._default_init(data, guildfile)

    def _dict_init(self, data, guildfile):
        assert isinstance(data, dict), data
        self._default_init(
            data.get("select"),
            guildfile,
            data.get("root"),
            data.get("digest"),
            data.get("dest"),
        )

    def _default_init(self, select_data, guildfile, root=None, digest=None, dest=None):
        self.disabled = select_data is False
        if select_data in (None, False):
            select_data = []
        if not isinstance(select_data, list):
            raise GuildfileError(
                guildfile,
                f"invalid file select spec {select_data!r}: expected "
                "a list or no/off",
            )
        self.root = root
        self.specs = [FileSelectSpec(item, guildfile) for item in select_data]
        self.digest = digest
        self.dest = dest


class FileSelectSpec:
    def __init__(self, data, guildfile):
        if not isinstance(data, dict):
            raise GuildfileError(
                guildfile, f"invalid file select spec {data!r}: expected a mapping"
            )
        if "include" in data and "exclude" in data:
            raise GuildfileError(
                guildfile,
                f"invalid file select spec {data!r}: cannot include both include "
                "and exclude - use multiple select specs in the order you "
                "want to apply the filters",
            )

        super().__init__()

        if "include" in data:
            self.type = "include"
            (self.patterns,
             self.patterns_type) = self._init_patterns(data, "include", guildfile)
        elif "exclude" in data:
            self.type = "exclude"
            (self.patterns,
             self.patterns_type) = self._init_patterns(data, "exclude", guildfile)
        else:
            raise GuildfileError(guildfile, f"unsupported file select spec: {data!r}")

    def _init_patterns(self, data, name, guildfile):
        config = data[name]
        if isinstance(config, (str, list)):
            return (_coerce_str_to_list(config, guildfile, name), None)
        if isinstance(config, dict):
            return self._init_typed_patterns(config, guildfile, name)
        raise GuildfileError(guildfile, f"unsupported {name} value: {config!r}")

    @staticmethod
    def _init_typed_patterns(data, guildfile, name):
        for type in ("dir", "text", "binary"):
            if type in data:
                return (_coerce_str_to_list(data[type], guildfile, name), type)
        raise GuildfileError(guildfile, f"unsupported {name} value: {config!r}")

    def __repr__(self):
        patterns = ",".join(self.patterns)
        return f"<guild.guildfile.FileSelectSpec {self.type} {patterns}>"


###################################################################
# Resource def
###################################################################


class ResourceDef(resourcedef.ResourceDef):
    """Resource def from a Guild file.

    Initialized using data (config) from a Guild file and is
    associated with a model def.
    """

    source_types = resourcedef.ResourceDef.source_types + ["operation"]

    def __init__(self, name, data, modeldef):
        try:
            super().__init__(name, data, _resdef_fullname(name, modeldef.name))
        except resourcedef.ResourceDefValueError:
            raise GuildfileError(
                modeldef.guildfile,
                f"invalid resource value {data!r}: expected a mapping or a list",
            ) from None
        except resourcedef.ResourceFormatError as e:
            raise GuildfileError(modeldef.guildfile, e) from e
        self.private = self.private
        self.modeldef = modeldef

    def _resource_source_for_data(self, data):
        try:
            return super()._resource_source_for_data(data)
        except resourcedef.ResourceFormatError:
            source = _try_plugins_for_resource_source_data(data, self)
            if not source:
                raise
            return source

    def _source_for_type(self, type, val, data):
        data = resourcedef.coerce_source_data(data)
        if type == "operation":
            return resourcedef.ResourceSource(self, f"operation:{val}", **data)
        return super()._source_for_type(type, val, data)


def _try_plugins_for_resource_source_data(data, resdef):
    from guild import plugin as pluginlib  # Expensive

    for _name, plugin in pluginlib.iter_plugins():
        source = plugin.resource_source_for_data(data, resdef)
        if source:
            return source
    return None


def _resdef_fullname(config_name, model_name):
    res_name = config_name if config_name else "<inline>"
    return f"{model_name}:{res_name}"


###################################################################
# Package def
###################################################################


class PackageDef:
    def __init__(self, name, data, guildfile):
        self.name = name
        self.guildfile = guildfile
        self.description = (data.get("description") or "").strip()
        self.version = data.get("version", DEFAULT_PKG_VERSION)
        self.url = data.get("url")
        self.author = data.get("author")
        self.author_email = data.get("author-email")
        self.license = data.get("license")
        self.tags = data.get("tags") or []
        self.python_tag = data.get("python-tag")
        self.data_files = data.get("data-files") or []
        self.python_requires = data.get("python-requires")
        self.requires = _coerce_str_to_list(
            data.get("requires") or [], guildfile, "requires"
        )
        self.packages = data.get("packages")

    def __repr__(self):
        return f"<guild.guildfile.PackageDef '{self.name}'>"


###################################################################
# Module API
###################################################################


def for_dir(path, no_cache=False):
    log.debug("checking '%s' for model sources", path)
    model_file = os.path.abspath(guildfile_path(path))
    if os.path.isfile(model_file):
        log.debug("found model source '%s'", model_file)
        return for_file(model_file, no_cache=no_cache)
    raise NoModels(path)


def is_guildfile_dir(path):
    return os.path.exists(guildfile_path(path))


def guildfile_path(*paths):
    if not paths:
        paths = (config.cwd(),)
    return os.path.join(*(paths + (NAME,)))


def for_file(src, extends_seen=None, no_cache=False):
    cache_key = _cache_key(src)
    if not no_cache:
        cached = _cache.get(cache_key)
        if cached:
            return cached
    guildfile = _load_guildfile(src, extends_seen)
    if not no_cache:
        _cache[cache_key] = guildfile
    return guildfile


def _cache_key(src):
    return os.path.realpath(src)


def _load_guildfile(src, extends_seen):
    try:
        data = yaml.safe_load(open(src, "r"))
    except yaml.YAMLError as e:
        if log.getEffectiveLevel() <= logging.DEBUG:
            log.exception("loading yaml from %s", src)
        raise GuildfileError(src, str(e)) from e
    else:
        _notify_plugins_guildfile_data(data, src)
        guildfile = Guildfile(data, src, extends_seen=extends_seen)
        _notify_plugins_guildfile_loaded(guildfile)
        return guildfile


def _notify_plugins_guildfile_data(data, src):
    from guild import plugin as pluginlib  # expensive

    for _name, plugin in pluginlib.iter_plugins():
        plugin.guildfile_data(data, src)


def _notify_plugins_guildfile_loaded(guildfile):
    from guild import plugin as pluginlib  # expensive

    for _name, plugin in pluginlib.iter_plugins():
        plugin.guildfile_loaded(guildfile)


def for_string(s, src="<string>"):
    data = yaml.safe_load(s)
    _notify_plugins_guildfile_data(data, src)
    return Guildfile(data, src)


def for_run(run):
    if run.opref.pkg_type == "guildfile":
        return _for_guildfile_ref(run)
    if run.opref.pkg_type == "package":
        return _for_package_ref(run.opref)
    raise TypeError(f"unsupported pkg_type for run ({run.dir}): {run.opref.pkg_type}")


def _for_guildfile_ref(run):
    guildfile_path = os.path.join(run.dir, run.opref.pkg_name)
    if not os.path.isfile(guildfile_path):
        raise GuildfileMissing(guildfile_path)
    return for_file(guildfile_path)


def _for_package_ref(opref):
    import pkg_resources

    try:
        dist = pkg_resources.get_distribution(opref.pkg_name)
    except pkg_resources.DistributionNotFound as e:
        raise GuildfileMissing(f"cannot find package '{opref.pkg_name}'") from e
    else:
        return _for_pkg_dist(dist, opref)


def _for_pkg_dist(dist, opref):
    guildfile_path = os.path.join(
        dist.location, opref.pkg_name.replace(".", os.path.sep), "guild.yml"
    )
    if not os.path.exists(guildfile_path):
        raise GuildfileMissing(guildfile_path)
    return for_file(guildfile_path)


def _maybe_apply_anonymous_model(data):
    assert isinstance(data, dict), data
    # Only apply anonymous model if data contains operations.
    if "operations" not in data:
        return
    for name in MODEL_TYPES:
        if name in data:
            return
    data["model"] = ""


def split_script_path(script_path, cwd=None):
    """Returns a tuple of guildfile directory and relative script path.

    Guildfile dir is the common path between the script path and `cwd`.
    If `cwd` is `None` (default) `config.cwd()` is used.
    """
    script_realpath = os.path.realpath(script_path)
    cwd_realpath = os.path.realpath(cwd or config.cwd())
    guildfile_dir = os.path.commonpath([script_realpath, cwd_realpath])
    rel_script_path = os.path.relpath(script_realpath, guildfile_dir)
    return guildfile_dir, rel_script_path

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

import hashlib
import importlib
import json
import logging
import os
import re
import subprocess
import tempfile

import yaml

import guild.opref

from guild import util
from guild import var
from guild import yaml_util

log = logging.getLogger("guild")

DEFAULT_MATCHING_RUN_STATUS = (
    "completed",
    "running",
    "terminated",
)

###################################################################
# Resolver base/core classes
###################################################################


class ResolutionError(Exception):
    pass


class ResolveContext:
    def __init__(self, run=None, unpack_dir=None):
        self.run = run
        self.unpack_dir = unpack_dir


class Resolver:
    def __init__(self, source, resource):
        self.source = source
        self.resource = resource

    def resolve(self, resolve_context):
        raise NotImplementedError()


###################################################################
# Resolver factory
###################################################################


def for_resdef_source(source, resource):
    cls = resolver_class_for_source(source)
    if not cls:
        return None
    return cls(source, resource)


def resolver_class_for_source(source):
    scheme = source.parsed_uri.scheme
    if scheme == "file":
        return FileResolver
    if scheme in ["http", "https"]:
        return URLResolver
    if scheme == "module":
        return ModuleResolver
    if scheme == "operation":
        return OperationResolver
    if scheme == "config":
        return ConfigResolver
    return _try_plugins_for_resolver_class(source)


def _try_plugins_for_resolver_class(source):
    from guild import plugin as pluginlib

    for _name, plugin in pluginlib.iter_plugins():
        cls = plugin.resolver_class_for_source(source)
        if cls:
            return cls
    return None


###################################################################
# File resolver
###################################################################


class FileResolver(Resolver):
    def resolve(self, resolve_context):
        if self.resource.config:
            return _resolve_config_path(self.resource.config, self.source.resdef.name)
        source_path = self._abs_source_path()
        unpack_dir = _unpack_dir(source_path, resolve_context.unpack_dir)
        resolved = self._resolve_source_files(source_path, unpack_dir)
        _check_source_resolved(resolved, self.source)
        post_process(self.source, unpack_dir or os.path.dirname(source_path))
        return resolved

    def _abs_source_path(self):
        source_path = self.source.parsed_uri.path
        for root in self._source_location_paths():
            abs_path = os.path.abspath(os.path.join(root, source_path))
            if os.path.exists(abs_path):
                return abs_path
        raise ResolutionError(f"cannot find source file '{source_path}'")

    def _resolve_source_files(self, source_path, unpack_dir):
        """Resolves source files for file resolver.

        If source_path is a directory and there are no selection
        criteria, the directory itself is returned as resolved. Note
        this is different from operation resolver, which returns list
        of root names in the selected run directory when there are no
        selection criteria.
        """
        if os.path.isdir(source_path) and not self.source.select:
            return [source_path]
        return resolve_source_files(source_path, self.source, unpack_dir)

    def _source_location_paths(self):
        assert self.resource.location, self.resource
        yield self.resource.location
        try:
            modeldef = self.resource.resdef.modeldef
        except AttributeError:
            pass
        else:
            for parent in modeldef.parents:
                yield parent.dir


###################################################################
# URL Resolver
###################################################################


class URLResolver(Resolver):
    def resolve(self, resolve_context):
        from guild import pip_util  # expensive

        if self.resource.config:
            return _resolve_config_path(self.resource.config, self.source.resdef.name)
        download_dir = url_source_download_dir(self.source)
        util.ensure_dir(download_dir)
        try:
            source_path = pip_util.download_url(
                self.source.uri, download_dir, self.source.sha256
            )
        except pip_util.HashMismatch as e:
            raise ResolutionError(
                f"bad sha256 for '{e.path}' (expected {e.expected} but got {e.actual})"
            ) from e
        except Exception as e:
            if log.getEffectiveLevel() <= logging.DEBUG:
                log.exception(self.source.uri)
            raise ResolutionError(e) from e
        else:
            unpack_dir = _url_unpack_dir(source_path, resolve_context.unpack_dir)
            resolved = resolve_source_files(source_path, self.source, unpack_dir)
            _check_source_resolved(resolved, self.source)
            post_process(self.source, unpack_dir or os.path.dirname(source_path))
            return resolved


def url_source_download_dir(source):
    key = "\n".join(source.parsed_uri).encode("utf-8")
    digest = hashlib.sha224(key).hexdigest()
    return os.path.join(var.cache_dir("resources"), digest)


def _url_unpack_dir(source_path, explicit_unpack_dir):
    return explicit_unpack_dir or os.path.dirname(source_path)


###################################################################
# Operation resolver
###################################################################


class OperationResolver(FileResolver):
    def resolve(self, resolve_context):
        run = self._resolve_run()
        unpack_dir = _unpack_dir(run.dir, resolve_context.unpack_dir)
        resolved = _resolve_run_files(run, self.source, unpack_dir)
        _check_source_resolved(resolved, self.source)
        return resolved

    def _resolve_run(self):
        run_spec = str(self.resource.config) if self.resource.config else ""
        if run_spec and os.path.isdir(run_spec):
            log.info("Using run %s for %s resource", run_spec, self.source.resdef.name)
            return run_spec
        run = self.resolve_op_run(run_spec)
        log.info("Using run %s for %s resource", run.id, self.source.resdef.name)
        return run

    def resolve_op_run(self, run_id_prefix=None, include_staged=False):
        return self._resolve_op_run(run_id_prefix, include_staged, marked_or_latest_run)

    def _resolve_op_run(self, run_id_prefix, include_staged, resolve_run_cb):
        oprefs = self._source_oprefs()
        status = _matching_run_status(include_staged)
        run = resolve_run_cb(oprefs, run_id_prefix, status)
        if not run:
            oprefs_desc = ",".join([self._opref_desc(opref) for opref in oprefs])
            raise ResolutionError(f"no suitable run for {oprefs_desc}")
        return run

    def _source_oprefs(self):
        oprefs = []
        for spec in self._split_opref_specs(self.source.parsed_uri.path):
            try:
                oprefs.append(guild.opref.OpRef.for_string(spec))
            except guild.opref.OpRefError as e:
                raise ResolutionError(f"inavlid operation reference {spec!r}") from e
        return oprefs

    @staticmethod
    def _split_opref_specs(spec):
        return [part.strip() for part in spec.split(",")]

    @staticmethod
    def _opref_desc(opref):
        if opref.pkg_type == "guildfile":
            pkg = "./"
        elif opref.pkg_name:
            pkg = opref.pkg_name + "/"
        else:
            pkg = ""
        model_spec = pkg + (opref.model_name or "")
        return f"{model_spec}:{opref.op_name}" if model_spec else opref.op_name


def _matching_run_status(include_staged):
    if include_staged:
        return DEFAULT_MATCHING_RUN_STATUS + ("staged",)
    return DEFAULT_MATCHING_RUN_STATUS


def marked_or_latest_run(oprefs, run_id_prefix=None, status=None):
    runs = matching_runs(oprefs, run_id_prefix, status)
    log.debug("runs for %s: %s", oprefs, runs)
    if not runs:
        return None
    for run in runs:
        if run.get("marked"):
            return run
    return runs[0]


def matching_runs(oprefs, run_id_prefix=None, status=None):
    status = status or DEFAULT_MATCHING_RUN_STATUS
    oprefs = [_resolve_opref(opref) for opref in oprefs]
    runs_filter = _runs_filter(oprefs, run_id_prefix, status)
    return var.runs(sort=["-started"], filter=runs_filter)


def _resolve_opref(opref):
    if not opref.op_name:
        raise RuntimeError(f"invalid opref: {opref}")
    return guild.opref.OpRef(
        pkg_type=opref.pkg_type or "package" if opref.pkg_name else None,
        pkg_name=opref.pkg_name,
        pkg_version=None,
        model_name=opref.model_name,
        op_name=opref.op_name,
    )


def _runs_filter(oprefs, run_id_prefix, status):
    if _is_full_run_id(run_id_prefix):
        return lambda run: run.id == run_id_prefix
    return var.run_filter(
        "all",
        [
            _run_id_prefix_filter(run_id_prefix),
            _run_status_filter(status),
            _run_opref_filter(oprefs),
        ],
    )


def _is_full_run_id(s):
    return s and isinstance(s, str) and len(s) == 32


def _run_id_prefix_filter(run_id_prefix):
    if run_id_prefix:
        assert isinstance(run_id_prefix, str), run_id_prefix
        return lambda run: run.id.startswith(run_id_prefix)
    return lambda _run: True


def _run_status_filter(status):
    return var.run_filter(
        "any", [var.run_filter("attr", "status", status_val) for status_val in status]
    )


def _run_opref_filter(oprefs):
    return var.run_filter("any", [opref_match_filter(opref) for opref in oprefs])


class opref_match_filter:
    def __init__(self, opref):
        self.opref = opref

    def __call__(self, run):
        return self.opref.is_op_run(run, match_regex=True)


def _resolve_run_files(run, source, unpack_dir):
    resolved = resolve_source_files(run.dir, source, unpack_dir)
    if not source.select:
        # If select not specified, ensure that result does not contain source
        # code files (i.e. contains only dependencies and generated files)
        return _filter_non_sourcecode_files(resolved, run)
    assert resolved


def _filter_non_sourcecode_files(paths, run):
    from guild import run_util

    sourcecode = set(run_util.sourcecode_files(run))
    is_sourcecode = lambda path: os.path.relpath(path, run.dir) in sourcecode
    return [path for path in paths if not is_sourcecode(path)]


###################################################################
# Module resolver
###################################################################


class ModuleResolver(Resolver):
    def resolve(self, resolve_context):
        module_name = self.source.parsed_uri.path
        try:
            importlib.import_module(module_name)
        except ImportError as e:
            raise ResolutionError(str(e)) from e
        else:
            return []


###################################################################
# Config resolver
###################################################################


class ConfigResolver(FileResolver):
    """Resolves config sources.

    Config sources are resolved by applying source params and flag
    vals to the config source file. A new config file is generated and
    stored in the run directory under `.guild/generated/RAND/CONFIG`.

    `CONFIG` is assumed to be a YAML file containing a root map
    element.

    Param and flag values are applied using the nesting rules
    implemented in `util.nested_config`. These use dot delimiters to
    designate additional levels in the config map.

    flag values take precedence over param values of the same name.

    Resolves sources are linked to link other resolved resources.
    """

    YAML_EXT = (".yml", ".yaml")
    JSON_EXT = (".json",)
    CFG_EXT = (".cfg", ".ini")
    ALL_EXT = YAML_EXT + JSON_EXT + CFG_EXT

    def resolve(self, resolve_context):
        if not resolve_context.run:
            raise TypeError("config resolver requires run for resolve context")
        resolved = super().resolve(resolve_context)
        return [self._generate_config(path, resolve_context) for path in resolved]

    def _generate_config(self, path, resolve_context):
        try:
            config = self._load_config(path)
        except Exception as e:
            raise ResolutionError(f"error loading config from {path}: {e}") from e
        else:
            log.debug("loaded config: %r", config)
            self._apply_params(config)
            self._apply_run_flags(config, resolve_context.run)
            target_path = self._init_target_path(path, resolve_context.run)
            log.debug("resolved config: %r", config)
            self._write_config(config, target_path)
            return target_path

    def _load_config(self, path):
        decoder = self._decoder_for_path(path)
        if not decoder:
            raise ResolutionError(f"unsupported file type for '{path}'")
        return decoder(path)

    @classmethod
    def _decoder_for_path(cls, path):
        ext = _config_file_ext(path)
        if ext in cls.YAML_EXT:
            return cls._yaml_load
        if ext in cls.JSON_EXT:
            return cls._json_load
        if ext in cls.CFG_EXT:
            return cls._cfg_load
        return None

    @staticmethod
    def _yaml_load(path):
        with open(path) as f:
            return yaml.safe_load(f)

    @staticmethod
    def _json_load(path):
        with open(path) as f:
            return json.load(f)

    @staticmethod
    def _cfg_load(path):
        import configparser

        config = configparser.ConfigParser()
        config.read(path)
        data = dict(config.defaults())
        for section in config.sections():
            for name in config.options(section):
                val = config.get(section, name)
                data[f"{section}.{name}"] = val
        return util.nested_config(data)

    def _apply_params(self, config):
        params = self.source.params
        if params:
            if not isinstance(params, dict):
                log.warning("unexpected params %r - cannot apply to config", params)
                return
            util.nested_config(params, config)

    def _apply_run_flags(self, config, run):
        flags = self._run_flags_for_config(run)
        flags_config = self._flags_config(run)
        self._apply_arg_split(flags_config, flags)
        self._apply_nested_config(flags, flags_config, config)

    @staticmethod
    def _run_flags_for_config(run):
        """Returns dict of flags with non-None values."""
        flags = run.get("flags") or {}
        return {name: val for name, val in flags.items() if val is not None}

    def _apply_arg_split(self, flags_config, flags):
        for name in flags:
            arg_split = flags_config.get(name, {}).get("arg-split")
            self._maybe_apply_flag_arg_split(arg_split, name, flags)

    @staticmethod
    def _flags_config(run):
        op_config = run.get("op") or {}
        return op_config.get("op-cmd", {}).get("cmd-flags", {})

    def _maybe_apply_flag_arg_split(self, arg_split, flag_name, flags):
        if not arg_split:
            return
        val = flags.get(flag_name)
        if not isinstance(val, str):
            return
        flags[flag_name] = self._split_encoded_list(val, arg_split)

    @staticmethod
    def _split_encoded_list(encoded, split_spec):
        from guild import flag_util

        split_val = flag_util.split_encoded_flag_val(encoded, split_spec)
        return [flag_util.decode_flag_val(part) for part in split_val]

    def _apply_nested_config(self, flags, flags_config, config):
        flag_with_applied_name = {
            self._apply_config_flag_name(name, flags_config): val
            for name, val in flags.items()
        }
        util.nested_config(flag_with_applied_name, config)

    @staticmethod
    def _apply_config_flag_name(name, flags_config):
        return flags_config.get(name, {}).get("arg-name") or name

    @staticmethod
    def _init_target_path(path, run):
        generated_dir = run.guild_path("generated")
        util.ensure_dir(generated_dir)
        target_dir = tempfile.mkdtemp(suffix="", prefix="", dir=generated_dir)
        basename = os.path.basename(path)
        return os.path.join(target_dir, basename)

    def _write_config(self, config, path):
        encode = self._encoder_for_path(path)
        with open(path, "w") as f:
            f.write(encode(config))

    @classmethod
    def _encoder_for_path(cls, path):
        ext = _config_file_ext(path)
        if ext in cls.YAML_EXT:
            return yaml_util.encode_yaml
        if ext in cls.JSON_EXT:
            return cls._json_encode
        if ext in cls.CFG_EXT:
            return cls._cfg_encode
        assert False, path

    @staticmethod
    def _json_encode(config_data):
        return json.dumps(config_data, sort_keys=True)

    @staticmethod
    def _cfg_encode(config_data):
        return util.encode_cfg(config_data)


def _config_file_ext(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".in":
        return _config_file_ext(path[:-3])
    return ext


###################################################################
# Resolve source files support
###################################################################


def resolve_source_files(source_path, source, unpack_dir):
    if not unpack_dir:
        raise ValueError("unpack_dir required")
    log.debug("resolving source files for '%s' from %s", source, source_path)
    if os.path.isdir(source_path):
        return _resolve_source_dir_files(source_path, source)
    return _resolve_source_file_or_archive_files(source_path, source, unpack_dir)


def _resolve_source_dir_files(source_path, source):
    if source.select:
        return _selected_dir_files(source_path, source.select)
    return _root_dir_files(source_path)


def _selected_dir_files(source_path, select):
    all_files = _all_dir_files(source_path)
    return _selected_source_paths(source_path, all_files, select)


def _all_dir_files(dir):
    all = []
    for root, dirs, files in os.walk(dir):
        root = os.path.relpath(root, dir) if dir != root else ""
        for name in dirs + files:
            path = os.path.join(root, name)
            normalized_path = path.replace(os.path.sep, "/")
            all.append(normalized_path)
    return all


def _selected_source_paths(root, paths, select):
    selected = set()
    paths = sorted(paths)
    for pattern_str, reduce_f in select:
        matches = _match_paths(paths, pattern_str)
        if reduce_f:
            matches = reduce_f(matches)
        selected.update([os.path.join(root, m.string) for m in matches])
    return sorted(selected)


def _match_paths(paths, pattern_str):
    try:
        p = re.compile(pattern_str + "$")
    except Exception as e:
        log.error("error compiling regular expression %r: %s", pattern_str, e)
        return []
    else:
        return [m for m in [p.match(path) for path in paths] if m]


def _root_dir_files(source_path):
    return _root_paths(source_path, os.listdir(source_path))


def _root_paths(root, files):
    root_names = {path.split("/")[0] for path in sorted(files)}
    return [
        os.path.join(root, name)
        for name in sorted(root_names)
        if not name.startswith(".guild")
    ]


def _resolve_source_file_or_archive_files(source_path, source, unpack_dir):
    _verify_path(source_path, source.sha256)
    if source.unpack:
        archive_type = _archive_type(source_path, source)
        if archive_type:
            return _resolve_archive_files(source_path, archive_type, source, unpack_dir)
        return [source_path]
    return [source_path]


def _verify_path(path, sha256):
    if not os.path.exists(path):
        raise ResolutionError(f"'{path}' does not exist")
    if sha256:
        if os.path.isdir(path):
            log.warning("cannot verify '%s' because it's a directory", path)
            return
        _verify_file_hash(path, sha256)


def _verify_file_hash(path, sha256):
    actual = util.file_sha256(path, use_cache=True)
    if actual != sha256:
        raise ResolutionError(
            f"'{path}' has an unexpected sha256 (expected {sha256} but got {actual})"
        )


def _archive_type(source_path, source):
    if source.type:
        return source.type
    parts = source_path.lower().split(".")
    if parts[-1] == "zip":
        return "zip"
    if parts[-1] == "tar" or parts[-1] == "tgz" or parts[-2:-1] == ["tar"]:
        return "tar"
    if parts[-1] == "gz":
        return "gzip"
    return None


def _resolve_archive_files(source_path, archive_type, source, unpack_dir):
    """Returns resolved files in an archive.

    If source has a select spec, it's applied to the contents of the
    archive to return a list of matching source paths. If source does
    not have a select spec, the root paths from archive members are
    returned.

    Directories are resolved, even though directories are not
    typically defined as archive members (archives store files -
    directories are implied by a file path).

    Only paths corresponding to archive members are returned. Files
    that are in unpack dir that are not members of the archive are not
    returned.
    """
    unpacked = _ensure_unpacked(source_path, archive_type, unpack_dir)
    if source.select:
        return _selected_source_paths(unpack_dir, unpacked, source.select)
    return _root_paths(unpack_dir, unpacked)


def _ensure_unpacked(source_path, archive_type, unpack_dir):
    assert unpack_dir
    cached = _read_cached_unpacked(source_path, unpack_dir)
    if cached:
        return cached
    unpacked = _unpack(source_path, archive_type, unpack_dir)
    _write_cached_unpacked(unpacked, unpack_dir, source_path)
    return unpacked


def _read_cached_unpacked(source_path, unpack_dir):
    cache_path = _unpacked_cache_path(unpack_dir, source_path)
    cache_time = util.getmtime(cache_path)
    if not cache_time or cache_time < util.getmtime(source_path):
        return None
    lines = open(cache_path, "r").readlines()
    return [l.rstrip() for l in lines]


def _unpacked_cache_path(unpack_dir, source_path):
    name = os.path.basename(source_path)
    return os.path.join(unpack_dir, f".guild-cache-{name}.unpacked")


def _unpack(source_path, archive_type, unpack_dir):
    if archive_type == "zip":
        return _unzip(source_path, unpack_dir)
    if archive_type == "tar":
        return _untar(source_path, unpack_dir)
    if archive_type == "gzip":
        return _gunzip(source_path, unpack_dir)
    raise ResolutionError(
        f"'{source_path}' cannot be unpacked "
        f"(unsupported archive type '{archive_type}')"
    )


def _unzip(src, unpack_dir):
    import zipfile

    zf = zipfile.ZipFile(src)
    log.info("Unpacking %s", src)
    return _gen_unpack(unpack_dir, zf.namelist, lambda name: name, zf.extractall)


def _untar(src, unpack_dir):
    import tarfile

    tf = tarfile.open(src)
    log.info("Unpacking %s", src)
    return _gen_unpack(
        unpack_dir, _tar_members_fun(tf), _tar_member_name, tf.extractall
    )


def _tar_members_fun(tf):
    def f():
        return [m for m in tf.getmembers() if m.name != "."]

    return f


def _tar_member_name(tfinfo):
    return _strip_leading_dotdir(tfinfo.name)


def _gunzip(src, unpack_dir):
    return _gen_unpack(
        unpack_dir,
        _gzip_list_members_fun(src),
        _gzip_member_name_fun,
        _gzip_extract_fun(src),
    )


def _gzip_list_members_fun(src):
    return lambda: [_gzip_member_name(src)]


def _gzip_member_name(src):
    assert src[-3:] == ".gz", src
    return os.path.basename(src)[:-3]


def _gzip_member_name_fun(m):
    return m


def _gzip_extract_fun(src):
    import gzip

    def extract(unpack_dir, members):
        if not members:
            return
        assert len(members) == 1, members
        member_name = members[0]
        assert _gzip_member_name(src) == member_name, (src, member_name)
        dest = os.path.join(unpack_dir, member_name)
        with gzip.open(src, "rb") as f_in:
            with open(dest, "wb") as f_out:
                while True:
                    block = f_in.read(102400)
                    if not block:
                        break
                    f_out.write(block)

    return extract


def _strip_leading_dotdir(path):
    if path[:2] == "./":
        return path[2:]
    return path


def _gen_unpack(unpack_dir, list_members, member_name, extract):
    members = list_members()
    names = [member_name(m) for m in members]
    to_extract = [
        member
        for member, name in zip(members, names)
        if not os.path.exists(os.path.join(unpack_dir, name))
    ]
    extract(unpack_dir, to_extract)
    return _dirs_for_unpack_names(names) + names


def _dirs_for_unpack_names(names):
    dirs = {name.rsplit("/", 1)[0] for name in names}
    names = set(names)
    return sorted(dirs - names)


def _write_cached_unpacked(unpacked, unpack_dir, source_path):
    cache_path = _unpacked_cache_path(unpack_dir, source_path)
    with open(cache_path, "w") as f:
        for path in unpacked:
            f.write(path + "\n")


###################################################################
# Post process support
###################################################################


def post_process(source, cwd, use_cache=True):
    if not source.post_process:
        return
    cmd_in = source.post_process.strip().replace("\n", " ")
    cmd = _apply_source_script_functions(cmd_in, source)
    if use_cache:
        cmd_digest = hashlib.sha1(cmd.encode()).hexdigest()
        process_marker = os.path.join(cwd, f".guild-cache-{cmd_digest}.post")
        if os.path.exists(process_marker):
            return
    log.info("Post processing %s resource in %s: %r", source.resdef.name, cwd, cmd)
    try:
        subprocess.check_call(cmd, shell=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        raise ResolutionError(
            f"error post processing {source.resdef.name} resource: {e}"
        ) from e
    else:
        util.touch(process_marker)


def _apply_source_script_functions(script, source):
    funs = [("project-src", (_project_src_source_script, [source]))]
    for name, fun in funs:
        script = _apply_source_script_function(name, fun, script)
    return script


def _apply_source_script_function(name, fun, script):
    return "".join(
        [
            _apply_source_script_function_to_part(part, name, fun)
            for part in _split_source_script(name, script)
        ]
    )


def _split_source_script(fun_name, script):
    return re.split(rf"(\$\({fun_name} .*?\))", script)


def _apply_source_script_function_to_part(part, fun_name, fun):
    m = re.match(rf"\$\({fun_name} (.*?)\)", part)
    if m is None:
        return part
    args = util.shlex_split(m.group(1))
    fun, extra_args = fun
    log.debug("Applying %s to %s", fun_name, args)
    return fun(*(args + extra_args))


def _project_src_source_script(path, source):
    roots = [_resdef_dir(source.resdef)] + _resdef_parent_dirs(source.resdef)
    for root in roots:
        full_path = os.path.join(root, path)
        if os.path.exists(full_path):
            log.debug("Found %s under %s", path, root)
            return full_path
    raise ResolutionError(
        f"project-src failed: could not find '{path}' "
        f"in path '{os.path.pathsep.join(roots)}'"
    )


def _resdef_dir(resdef):
    """Return directory for a resource definition.

    The ResourceDef interface doesn't provide a directory, but we can
    infer a directory by checking for 'modeldef' and 'dist'
    attributes, both of which are associated with a Guild file and
    therefore a directory.
    """
    if hasattr(resdef, "modeldef"):
        return resdef.modeldef.guildfile.dir
    if hasattr(resdef, "dist"):
        return resdef.dist.guildfile.dir
    raise AssertionError(resdef)


def _resdef_parent_dirs(resdef):
    try:
        modeldef = resdef.modeldef
    except AttributeError:
        return []
    else:
        return [parent.dir for parent in modeldef.parents]


###################################################################
# Utils / helpers
###################################################################


def _unpack_dir(source_path, explicit_unpack_dir):
    """Returns unpack dir for local archives.

    If explicit_unpack_dir is specified (non blank) it is always
    used. Otherwise a location under the resource cache is used
    based on the value of source_path. In this case, source_path
    must be absolute.

    As with downloaded archives, local archives are unacked into a
    resource cache dir. This avoid unpacking project local files
    within the project.

    """
    if explicit_unpack_dir:
        return explicit_unpack_dir
    assert os.path.isabs(source_path), source_path
    digest = _file_source_digest(source_path)
    return os.path.join(var.cache_dir("resources"), digest)


def _file_source_digest(path):
    key = "\n".join(["file", path]).encode("utf-8")
    return hashlib.sha224(key).hexdigest()


def _resolve_config_path(config, resource_name):
    config_path = os.path.abspath(str(config))
    if not os.path.exists(config_path):
        raise ResolutionError(f"{config_path} does not exist")
    log.info("Using %s for %s resource", os.path.relpath(config_path), resource_name)
    return [config_path]


def _check_source_resolved(resolved, source):
    if resolved:
        return
    if source.fail_if_empty:
        raise ResolutionError(f"nothing resolved for {source.name}")
    if source.warn_if_empty:
        log.warning("nothing resolved for %s", source.name)

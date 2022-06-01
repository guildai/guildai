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

from guild import manifest
from guild import util
from guild import var


def sourcecode_args(run_file, run_dir, project_file, project_dir):
    """Returns manifest args for a source code file.

    Args:

        ['s', run_relative_path, sha1, project_relative_path]

    """
    dest_arg = os.path.relpath(run_file, run_dir)
    hash_arg = util.file_sha1(run_file)
    src_arg = os.path.relpath(project_file, project_dir)
    return ["s", dest_arg, hash_arg, src_arg]


def resolved_source_args(resolved):
    """Returns manifest args for a resolved resource source (dependency).

    Args:

        ['d', run_relative_path, sha1_or_dash] + source_args

    If the resolved source is a file, its sha1 is included in the args
    at position 3, otherwise a dash ('-') is used.

    `source_args` in this is one of:

        - [source_uri]
        - [source_uri, subpath]

    Project local files are represented by
    `file:<project_relative_path>`. Other URIs are listed as they
    appear in the source configuration.

    When a source is an archive, the URI is followed by the
    archive-relative subpath to the resolved source.
    """
    dest_arg = os.path.relpath(resolved.target_path, resolved.target_root)
    hash_arg = _resolved_source_hash_manifest_arg(resolved.target_path)
    src_args = _resolved_source_src_manifest_args(resolved)
    return ["d", dest_arg, hash_arg] + src_args


def _resolved_source_hash_manifest_arg(target_path):
    if os.path.isfile(target_path):
        return util.file_sha1(target_path)
    return "-"


def _resolved_source_src_manifest_args(resolved):
    if _is_project_local_source(resolved):
        return ["file:" + _project_relpath(resolved)]
    else:
        return _resolved_source_uri_args(resolved)


def _is_project_local_source(resolved_source):
    return resolved_source.source_path.startswith(resolved_source.source_origin)


def _project_relpath(resolved_source):
    return os.path.relpath(resolved_source.source_path, resolved_source.source_origin)


def _resolved_source_uri_args(resolved_source):
    source_uri_file = _source_uri_file(resolved_source.source)
    source_relpath = _try_resource_cache_relpath(resolved_source.source_path)
    return [source_uri_file, source_relpath] if source_relpath else [source_uri_file]


def _source_uri_file(source):
    if source.parsed_uri.scheme == "file":
        return "file:" + source.parsed_uri.path
    return source.uri


def _try_resource_cache_relpath(source_path):
    """Tries to return the source path relative to a resource cache dir.

    Returns None if the source is not under the resource cache root.

    This is a best attempt to determine a resource source subpath
    based on where the source is extracted in a resource cache. This
    value is useful relative to the resource URI. For example, if a
    resource URI is 'file:files.zip' and the source is
    'aaa/bbb/file.txt' within that resource, this function attempts to
    return 'aaa/bbb/file.txt' based on the location of the resolved
    source file under a resource cache directory.

    Ideally we'd have this relative path in
    `guild.op_dep.ResolvedSource` but this would require a change to
    the `guild.resolver.Resolver.resolve()` interface. This function
    makes a best attempt to get this information at arm's length.
    """
    resource_root = var.cache_dir("resources")
    if source_path.startswith(resource_root):
        return _strip_resource_hash(os.path.relpath(source_path, resource_root))
    return None


def _strip_resource_hash(relpath):
    """Removes the first part of relpath, assuming it's s resource hash.

    Asserts length of hash to validate this assumption.
    """
    parts = relpath.split(os.path.sep)
    # If this assertion fails, the scheme used for resource caching
    # hash possibly changed (e.g. overridden to use another scheme or
    # the hash algorithm changed, etc.)
    assert parts and len(parts[0]) == 56, parts
    return os.path.sep.join(parts[1:])


def run_manifest_path(run_dir):
    return os.path.join(run_dir, ".guild", "manifest")


def manfiest_for_run(run, mode="r"):
    return manifest.Manifest(run_manifest_path(run.dir), mode)

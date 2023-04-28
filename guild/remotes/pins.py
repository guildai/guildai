import logging
import os
import re
import shutil
import sys
import tempfile
import zipfile

import pins

from guild import remote as remotelib
from guild import var
from guild import remote_util

from . import meta_sync

log = logging.getLogger("guild.remotes.pins")

RUNS_PATH = ["runs"]


class PinsRemoteType(remotelib.RemoteType):
    def __init__(self, _ep):
        pass

    def remote_for_config(self, name, config):
        return PinsRemote(name, config)

    def remote_for_spec(self, spec):
        pass


class PinsRemote(meta_sync.MetaSyncRemote):
    def __init__(self, name, config):
        self.name = name
        self.board = _init_board(config)
        self.subdir = config.get("subdir", "")
        local_sync_dir = meta_sync.local_meta_dir(name, str(config))
        runs_dir = os.path.join(local_sync_dir, *RUNS_PATH)
        super().__init__(runs_dir)

    def status(self, verbose=False):
        try:
            self.board.pin_list()
        except FileNotFoundError as e:
            raise remotelib.Down(f"{e.filename} does not exist")
        except Exception as e:
            raise remotelib.Down(e)
        else:
            sys.stdout.write(f"{self.name} (board {self.board.board}) is available\n")

    def _sync_runs_meta(self, force=False):
        remote_util.remote_activity(f"Refreshing run info for {self.name}")
        runs = self.board.pin_search(self.subdir or None)
        self._clear_runs_meta_dir()
        for _index, run in runs.iterrows():
            meta_string = run.meta.user.get("guild_meta")
            if meta_string is None:
                continue
            with tempfile.NamedTemporaryFile(mode="wb") as temp:
                temp.write(bytes(meta_string))
                temp.flush()
                with zipfile.ZipFile(temp.name, mode="r") as zip_ref:
                    expath = os.path.relpath(run["name"], self.subdir)
                    path = os.path.join(self._runs_dir, expath, "")
                    zip_ref.extractall(path)

    def _clear_runs_meta_dir(self):
        for root, dirs, files in os.walk(self._runs_dir):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))

    def _purge_runs(self, runs):
        raise NotImplementedError(
            "Pins doesn't support non permanent deletion of runs."
        )

    def _restore_runs(self, runs):
        raise NotImplementedError(
            "Pins doesn't support non permanent deletion of runs."
        )

    def push(self, runs, delete=False):
        remote_util.remote_activity("Pushing runs to pins board")
        for run in runs:
            self._push_run(run, delete)
        self._sync_runs_meta()

    def _push_run(self, run, delete):
        if not delete and self.board.pin_exists(self._get_run_pin_name(run.id)):
            log.info(
                "Run %s already exists in pins board, skipping",
                self._get_run_pin_name(run.id)
            )
            return

        with tempfile.TemporaryDirectory() as outdir:
            archive_path = self._archive_run_dir(run.path, outdir)
            metadata = self._archive_run_meta(run.path)
            # TODO Currently pins doesn't support uploading files, so
            # we read the archive into a binary string and use
            # pin_write to upload it.
            with open(archive_path, mode="rb") as f:
                data = list(f.read())
            self.board.pin_write(
                data,
                type="json",
                name=self._get_run_pin_name(run.id),
                versioned=True,
                metadata={"guild_meta": metadata}
            )

    def _archive_run_dir(self, dir, outfile):
        return shutil.make_archive(outfile, "zip", dir)

    def _archive_run_meta(self, run_path):
        with tempfile.NamedTemporaryFile() as tmp:
            with zipfile.ZipFile(tmp.name, "w") as zf:
                for root, _, files in os.walk(run_path):
                    for file in files:
                        fname = os.path.join(root, file)
                        relpath = os.path.relpath(fname, run_path)
                        if meta_sync.is_meta_file(fname):
                            zf.write(fname, relpath)
            # now read the zip file into a bytestring
            with open(tmp.name, "rb") as f:
                data = f.read()
            return data

    def pull(self, runs, delete=False):
        if delete:
            raise ValueError("Unsupported delete op.")
        for run in runs:
            self._pull_run(run)

    def _pull_run(self, run):
        archive = self.board.pin_read(self._get_run_pin_name(run.id))
        with tempfile.NamedTemporaryFile(mode="wb") as temp:
            temp.write(bytes(archive))
            with zipfile.ZipFile(temp.name, mode="r") as zip_ref:
                zip_ref.extractall(os.path.join(var.runs_dir(), run.id, ""))

    def _delete_runs(self, runs, permanent):
        assert permanent
        for run in runs:
            try:
                self.board.pin_delete(self._get_run_pin_name(run.id))
            except pins.errors.PinsError as e:
                log.warning(
                    "Failed to delete run %s: %s", self._get_run_pin_name(run.id), e
                )
            except:
                log.warning(
                    "Failed to delete run %s. Unknown error",
                    self._get_run_pin_name(run.id)
                )

    def _get_run_pin_name(self, run_id):
        return os.path.join(self.subdir, run_id)


def _init_board(config):
    board_type, board_config = _split_remote_config(config)
    _fail_on_temp_type(board_type)
    _fail_on_relative_path(board_type, board_config)
    try:
        init_f = getattr(pins, f"board_{board_type}")
    except AttributeError:
        raise remotelib.ConfigError(
            f"unsupported board type '{board_type}' - refer to "
            "https://rstudio.github.io/pins-python/api/constructors "
            "for list of supported types"
        ) from None
    try:
        return init_f(**board_config)
    except TypeError as e:
        missing_params = _missing_params_for_type_error(e)
        if not missing_params:
            raise
        raise remotelib.ConfigError(
            f"board type '{board_type}' requires the following "
            f"config: {missing_params}"
        ) from None


def _split_remote_config(config):
    """Returns a tuple of board type and board config for remote config.

    Board type, which is required, is specified as `board-type`. The
    remaining values in config are used as board config.
    """
    config = remote_util.strip_common_config(config)
    board_type, config = config.pop_config("board-type")
    return board_type, config


def _fail_on_temp_type(board_type):
    if board_type == "temp":
        raise remotelib.ConfigError(
            "pins remote does not support temp boards - "
            "use a folder board pointing to a temp directory instead"
        )


def _fail_on_relative_path(board_type, board_config):
    if board_type == "folder":
        path = board_config.get("path")
        if path is not None and not os.path.isabs(path):
            raise remotelib.ConfigError(f"folder paths cannot be relative ({path})")


def _missing_params_for_type_error(e):
    m = re.search(r"required positional arguments?: (.*)", str(e))
    return m.group(1).replace("'", "") if m else None

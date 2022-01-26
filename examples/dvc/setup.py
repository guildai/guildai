import argparse
import os
import shutil
import subprocess


def main():
    args = _init_args()
    _init_dest(args)
    _init_git(args)
    _init_dvc(args)
    _config_dvc(args)
    _copy_source_code(args)
    _git_first_commit(args)


def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("dest", metavar="DEST", help="Directory to setup example in.")
    return p.parse_args()


def _init_dest(args):
    print("Initializing {}".format(args.dest))
    if not os.path.exists(args.dest):
        os.makedirs(args.dest)


def _init_git(args):
    print("Initializing Git")
    _ = subprocess.check_output(["git", "init"], cwd=args.dest)


def _init_dvc(args):
    print("Initializing DvC")
    _ = subprocess.check_output(["dvc", "init"], cwd=args.dest)


def _config_dvc(args):
    shutil.copyfile("dvc.config.in", os.path.join(args.dest, ".dvc", "config"))


def _copy_source_code(args):
    print("Copying source code files")
    for path in _git_ls_files():
        shutil.copyfile(path, os.path.join(args.dest, path))


def _git_ls_files():
    out = subprocess.check_output(["git", "ls-files"], encoding="utf-8")
    for line in out.split("\n"):
        line = line.strip()
        if line:
            yield line


def _git_first_commit(args):
    print("Creating first Git commit")
    _ = subprocess.check_output(["git", "add", "."], cwd=args.dest)
    _ = subprocess.check_output(["git", "commit", "-m", "First commit"], cwd=args.dest)


if __name__ == "__main__":
    main()

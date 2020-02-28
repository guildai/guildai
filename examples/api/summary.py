import argparse
import os

import pandas as pd

from guild import ipy as guild


def main():
    args = _init_args()
    runs = _best_runs(args)
    _summarize(runs)
    _link_runs(runs, args)


def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("--use-marked", action="store_true")
    p.add_argument("--min-loss", type=float, default=-0.2)
    p.add_argument("--output", default=".")
    return p.parse_args()


def _best_runs(args):
    runs = guild.runs(operations=["op"], marked=args.use_marked).compare()
    if runs.empty:
        return runs
    return runs[runs["loss"] <= args.min_loss]


def _summarize(runs):
    with pd.option_context("display.max_columns", None, "display.width", None):
        print(runs)


def _link_runs(runs, args):
    for _, row in runs.iterrows():
        _link_run(row.run.run, args)


def _link_run(run, args):
    os.symlink(run.dir, os.path.join(args.output, run.id))


if __name__ == "__main__":
    main()

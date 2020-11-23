"""Generate a TensorFlow Data Validation schema for data.

This module can be run as a Python script. Try `python -m gen_schema
--help` for command help.
"""


import argparse
import os

import tensorflow_data_validation as tfdv
import tensorflow_data_validation.utils.display_util as tfdv_display_util


def main():
    args = _init_args()
    stats = _gen_tfdv_stats(args)
    _gen_tfdv_schema(stats, args)


def _init_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data-path", default="data/train/data.csv")
    p.add_argument("--output-dir", default=".")
    return p.parse_args()


def _gen_tfdv_stats(args):
    stats = tfdv.generate_statistics_from_csv(data_location=args.data_path)
    _save_tfdv_stats_html(stats, args)
    return stats


def _save_tfdv_stats_html(stats, args):
    html = tfdv_display_util.get_statistics_html(stats)
    html_path = _output_path("tfdv-stats.html", args)
    with open(html_path, "w") as f:
        f.write(html)


def _output_path(filename, args):
    return os.path.join(args.output_dir, filename)


def _gen_tfdv_schema(stats, args):
    schema = tfdv.infer_schema(stats)
    _save_tfdv_schema(schema, args)
    return schema


def _save_tfdv_schema(schema, args):
    with open(_output_path("schema.pb", args), "wb") as f:
        f.write(schema.SerializeToString())
    _save_tfdv_schema_info(schema, args)


def _save_tfdv_schema_info(schema, args):
    features, domains = _tfdv_schema_info(schema)
    with open(_output_path("schema-features.txt", args), "w") as f:
        f.write(features.to_string())
    with open(_output_path("schema-domains.txt", args), "w") as f:
        f.write(domains.to_string())


def _tfdv_schema_info(schema):
    with TFDVSchemaDisplay() as display:
        tfdv.display_schema(schema)
        assert len(display.display_obj) == 2, display.display_obj
        return display.display_obj


class TFDVSchemaDisplay(object):
    """Patch tfdv_display_util.display to get generated dataframes.

    tfdv_display_util.display prints to IPython.display, which is not
    what we want. Instead, we want the dataframes being
    displayed. These can be used for analysis, saving, etc.

    Use `display_obj` to return all of the objects used in calls to
    tfdv_display_util.display.

    Patch is unapplied when the context manager exits.
    """

    def __init__(self):
        self._display_save = None
        self.display_obj = []

    def __enter__(self):
        self._display_save = tfdv_display_util.display
        tfdv_display_util.display = self._display
        return self

    def _display(self, obj):
        self.display_obj.append(obj)

    def __exit__(self, *_exc):
        tfdv_display_util.display = self._display_save


if __name__ == "__main__":
    if os.getenv("GUILD_RUN") == "1":
        from guild import ipy as guild

        guild.run(main)
    else:
        main()

# Copyright 2017-2020 TensorHub, Inc.
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

from __future__ import absolute_import
from __future__ import division

import csv
import os
import subprocess
import time

from guild import cli
from guild import util


def compare_runs(get_data_cb):
    cli.out("Preparing data for compare", err=True)
    hiplot = _hiplot_include_exe()
    data = get_data_cb()
    _format_data_for_hiplot(data)
    html_path_env = os.getenv("HIPLOT_HTML")
    if html_path_env:
        _handle_html_env(hiplot, data, html_path_env)
    else:
        _handle_default(hiplot, data)


def _handle_html_env(hiplot, data, html_path):
    with util.TempDir("guild-compare-") as tmp:
        csv_path = _hiplot_data_path(tmp.path)
        _write_hiplot_data(data, csv_path)
        _generate_hiplot_html(hiplot, csv_path, html_path)
        cli.out("Saved HiPlot HTML to %s" % html_path, err=True)


def _handle_default(hiplot, data):
    with util.TempDir("guild-compare-") as tmp:
        csv_path = _hiplot_data_path(tmp.path)
        _write_hiplot_data(data, csv_path)
        html_path = _hiplot_html_path(tmp.path)
        _generate_hiplot_html(hiplot, csv_path, html_path)
        cli.out("Opening %s" % html_path, err=True)
        util.open_url(html_path)
        cli.out("To return to the prompt, press Ctrl-C", err=True)
        _wait_forever()


def _hiplot_include_exe():
    exe = os.getenv("HIPLOT_RENDER")
    if exe:
        if os.path.exists(exe):
            return exe
        cli.error(
            "%s specified by HIPLOT_RENDER environment variable does not exist" % exe
        )
    exe = util.which("hiplot-render")
    if exe:
        return exe
    cli.error(
        "cannot find hiplot-render\n"
        "If HiPlot is installed, specified the path to hiplot-render "
        "using the HIPLOT_RENDER environment variable or install it "
        "by running 'pip install hiplot'."
    )


def _format_data_for_hiplot(data):
    assert data[0][0] == "run", data[0]
    data[0][0] = "uid"


def _hiplot_data_path(dir):
    return os.path.join(dir, "data.csv")


def _write_hiplot_data(data, path):
    with open(path, "w") as f:
        writer = csv.writer(f, lineterminator="\n")
        for row in data:
            writer.writerow(row)


def _hiplot_html_path(dir):
    return os.path.join(dir, "compare.html")


def _generate_hiplot_html(hiplot_include, csv_path, html_path):
    try:
        html = subprocess.check_output([hiplot_include, "--format", "html", csv_path])
    except subprocess.CalledProcessError as e:
        cli.error("error running %s: %s" % (hiplot_include, e))
    with open(html_path, "wb") as f:
        f.write(html)
    return html_path


def _wait_forever():
    while True:
        time.sleep(1000)

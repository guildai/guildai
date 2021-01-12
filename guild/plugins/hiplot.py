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
import logging
import os
import time

from guild import util

log = logging.getLogger("guild")


def compare_runs(get_data_cb):
    _check_hiplot_install()
    log.info("Preparing data for compare")
    data = get_data_cb()
    _format_data_for_hiplot(data)
    html_path_env = os.getenv("HIPLOT_HTML")
    if html_path_env:
        _handle_html_env(data, html_path_env)
    else:
        _handle_default(data)


def _check_hiplot_install():
    try:
        import hiplot as _
    except ImportError:
        raise SystemExit(
            "HiPlot is not available\nInstall it by running 'pip install hiplot'"
        )


def _handle_html_env(data, html_path):
    with util.TempDir("guild-compare-") as tmp:
        csv_path = _hiplot_data_path(tmp.path)
        _write_hiplot_data(data, csv_path)
        _generate_hiplot_html(csv_path, html_path)
        log.info("Saved HiPlot HTML to %s", html_path)


def _handle_default(data):
    with util.TempDir("guild-compare-") as tmp:
        csv_path = _hiplot_data_path(tmp.path)
        _write_hiplot_data(data, csv_path)
        html_path = _hiplot_html_path(tmp.path)
        _generate_hiplot_html(csv_path, html_path)
        log.info("Opening %s", html_path)
        util.open_url(html_path)
        log.info("To return to the prompt, press Ctrl-C")
        _wait_forever()


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


def _generate_hiplot_html(csv_path, html_path):
    # pylint: disable=import-error
    from hiplot import fetchers  # ImportError should be handled upstream.

    exp = fetchers.load_xp_with_fetchers(fetchers.get_fetchers([]), csv_path)
    exp.validate()
    with open(html_path, "w", encoding="utf-8") as f:
        exp.to_html(f)


def _wait_forever():
    while True:
        time.sleep(1000)

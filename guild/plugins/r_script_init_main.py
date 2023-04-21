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

import sys
import typing

from guild.plugins import r_util


def main():
    print("Installing R package 'guildai'")
    install_script = """
        if (file.access(.libPaths()[[1L]], 2) != 0L)
        local({
            # if default lib not writable, try create user lib dir
            userlibs <- strsplit(Sys.getenv("R_LIBS_USER"), .Platform$path.sep)[[1L]]
            if (!length(userlibs)) return()
            if (userlibs[[1L]] == "NULL") return()
            dir.create(userlibs[[1L]], recursive = TRUE, showWarnings = FALSE)
            .libPaths(userlibs[[1L]])
        })

        local({
            repos <- getOption("repos")
            if (identical(repos["CRAN"], "@CRAN@")) {
                repos["CRAN"] <- "https://cran.rstudio.com/"
                options(repos = repos)
            }
        })

        install_dev_version <- TRUE

        if (install_dev_version) {
            if (!require("remotes", quietly = TRUE)) {
                utils::install.packages("remotes")
            }
            remotes::install_github("guildai/guildai-r")
        } else {
            utils::install.packages("guildai")
        }
    """

    try:
        r_util.run_r(infile=install_script)
    except r_util.RScriptProcessError as e:
        _install_error(e)


def _install_error(e) -> typing.NoReturn:
    print(e.error_output.rstrip(), file=sys.stderr)
    raise SystemExit(e.returncode)


if __name__ == "__main__":
    main()

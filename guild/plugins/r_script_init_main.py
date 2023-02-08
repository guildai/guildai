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

# from guild import cli
from guild.plugins.r_script import run_r


def main():
    print("Installing R package 'guildai' ...",  end="")

    install_pkg_R_snippet = """
        if (file.access(.libPaths()[[1L]], 2) != 0L)
        local({
            # if default lib not writable, try create user lib dir
            userlibs <- strsplit(Sys.getenv("R_LIBS_USER"), .Platform$path.sep)[[1L]]
            if (length(userlibs) && userlibs[[1L]] != "NULL")
            dir.create(userlibs[[1L]], recursive = TRUE, showWarnings = FALSE)
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
            if (!require("remotes", quietly = TRUE))
                utils::install.packages("remotes")

            remotes::install_github("guildai/guildai-r")
        } else {

        # install_cran_release_version
            utils::install.packages("guildai")
        }

    """
    run_r(infile=install_pkg_R_snippet)
    print(" Done!")

    # cli.error("The 'guildai' R package is not available.")


if __name__ == "__main__":
    main()

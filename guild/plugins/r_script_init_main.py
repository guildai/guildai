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
# from guild.plugins.r_script import run_r


def main():
    print("TODO: install ze package")

    # consent = cli.confirm(". Continue?", True)
    # if consent:

    #     run_r(
    #         infile="""
    #     if(!require("remotes", quietly = TRUE))
    #         utils::install.packages("remotes", repos = c(CRAN = "https://cran.rstudio.com/"))

    #     install_github("t-kalinowski/guildai-r")
    #     """
    #     )

    #     # Still need to figure out the appropriate home for this r package
    #     # if we bundle it w/ the python module we could install with something like:
    #     #   path_r_pkg_src_dir = resolve_using(__path__)
    #     #   run_r('remotes::install_local("%s")' % path_r_pkg_src_dir)
    #     # or we could pull from cran directly:
    #     #  'utils::install.packages("guildai", repos = c(CRAN = "https://cran.rstudio.com/"))'
    #     #  or install w/o the remotes, but then we'll have to resolve
    #     #  R dep pkgs (e.g., jsonlite) manually first
    #     # 'utils::install.packages("%s", repos = NULL, type = "source")' % path_to_r_pkg_src

    #     return

    # cli.error("The 'guildai' R package is not available.")


if __name__ == "__main__":
    main()

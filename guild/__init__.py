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

__pkgdir__ = os.path.dirname(os.path.dirname(__file__))


if os.environ.get("DEBUG", "0") == "1":

    import debugpy

    debugpy.listen(5678)
    print("Waiting for debugger attach")
    debugpy.wait_for_client()
    print("Client connected!")
# insert breakpoints by clicking line numbers in vscode left side gutter,
# or insert breakpoint manually:
#   import debugpy; debugpy.breakpoint()


from ._version import __version__

# Copyright 2017-2019 TensorHub, Inc.
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

import numpy as np

def f(x):
    #import pdb;pdb.set_trace()
    return (np.sin(5 * x[0]) * (1 - np.tanh(x[0] ** 2)) *
            np.random.randn() * 0.1)

def cb(res):
    print("Trial: %s %s %s" % (res.x_iters, res.x, res.fun))

def main():
    import skopt
    res = skopt.dummy_minimize(
        f,
        [(-2.0, 2.0)],
        n_calls=10,
        callback=cb)
    #import pdb;pdb.set_trace()
    print("Best: %s -> %s" % (res.x, res.fun))

if __name__ == "__main__":
    main()

from __future__ import print_function

import numpy as np

x = 0.1

f = np.poly1d([1, -2, -28, 28, 12, -26, 100])
loss = f(x) * 0.05

print("loss: %f" % loss)

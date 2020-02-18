import numpy as np

x = 1.0
loss = (np.sin(5 * x) * (1 - np.tanh(x ** 2)) + np.random.randn() * 0.1)

print("loss: %f" % loss)

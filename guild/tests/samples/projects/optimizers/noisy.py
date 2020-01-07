import numpy as np

x = 0.1
noise = 0.1

print("x: %f" % x)
print("noise: %s" % noise)


def f(x):
    return np.sin(5 * x) * (1 - np.tanh(x ** 2)) + np.random.randn() * noise


loss = f(x)

print("loss: %f" % loss)

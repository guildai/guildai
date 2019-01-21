import numpy as np

x = 0.1

def f(x):
    return (np.sin(5 * x) * (1 - np.tanh(x ** 2)) *
            np.random.randn() * 0.1)

print("noisy(%f): %f" % (x, f(x)))

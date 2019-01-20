import numpy as np

x = 0.0

def f(x):
    return (np.sin(5 * x) * (1 - np.tanh(x ** 2)) *
            np.random.randn() * 0.1)

print(f(x))

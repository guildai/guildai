import numpy as np
noise = 0.1
x = 0
loss = (np.sin(5 * x) * (1 - np.tanh(x ** 2)) + np.random.randn() * noise)
print(f'loss: {loss}')

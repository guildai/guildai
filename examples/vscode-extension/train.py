import numpy as np

# Hyperparameters
x = 0.1
noise = 0.3

print("x: %f" % x)
print("noise: %f" % noise)

# Simulated training loss
loss = np.sin(6 * x) * (1 - np.tanh(x**2)) + np.random.randn() * noise

print("loss: %f" % loss)

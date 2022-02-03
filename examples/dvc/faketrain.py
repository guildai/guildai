import json
import os

import numpy as np

if os.path.exists("params.json"):
    params = json.load(open("params.json"))
else:
    params = json.load(open("params.json.in"))

# Hyperparameters
x = params.get("x", 0.1)
noise = params.get("noise", 0.1)

print("x: %f" % x)
print("noise: %f" % noise)

# Simulated training loss
loss = (np.sin(5 * x) * (1 - np.tanh(x ** 2)) + np.random.randn() * noise)

print("loss: %f" % loss)
with open("summary.json", "w") as f:
    json.dump({"loss": loss}, f)

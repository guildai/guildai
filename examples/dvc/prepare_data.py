import pickle

import numpy as np

species_map = {
    b"Iris-setosa": 0.0,
    b"Iris-versicolor": 1.0,
    b"Iris-virginica": 2.0,
}

print("Saving iris.npy")
data = np.genfromtxt(
    "iris.csv",
    delimiter=",",
    skip_header=1,
    dtype=np.dtype("float64"),
    usecols=(1, 2, 3, 4, 5),
    converters={5: lambda s: species_map.get(s)},
)
np.save("iris.npy", data)

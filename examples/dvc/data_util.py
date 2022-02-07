import numpy as np

def load_data():
    data = np.load("iris.npy")
    return data[:, :2], data[:, 4]

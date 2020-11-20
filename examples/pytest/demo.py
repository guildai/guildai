# Credit: https://scikit-learn.org/stable/modules/preprocessing.html

import warnings

from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn import preprocessing

default_random_state = 0


def prepare_data(random_state=default_random_state):
    X, y = load_iris(return_X_y=True)
    return train_test_split(X, y, random_state=random_state)


def test_prepare_data():
    data = prepare_data()
    assert len(data) == 4
    x_train, x_test, y_train, y_test = data
    assert len(x_train) == 112
    assert len(x_test) == 38
    assert len(y_train) == 112
    assert len(y_test) == 38


def transform(train, test, random_state=default_random_state):
    qt = preprocessing.QuantileTransformer(random_state=random_state)
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning)
        return (qt.fit_transform(train), qt.fit_transform(test))


def test_transform():
    import numpy as np

    data = prepare_data()
    assert len(data) == 4
    train, test, _, _ = data
    transformed = transform(train, test)
    assert len(transformed) == 2
    transformed_train, transformed_test = transformed
    assert len(transformed_train) == 112
    assert len(transformed_test) == 38
    p = np.percentile(transformed_train[:, 0], [0, 25, 50, 75, 100])
    assert len(p) == 5
    assert 0 <= p[0] < 0.05, p
    assert 0.2 < p[1] < 0.3, p
    assert 0.45 < p[2] < 0.55, p
    assert 0.7 < p[3] < 0.8, p
    assert 0.95 < p[4] <= 1.0, p

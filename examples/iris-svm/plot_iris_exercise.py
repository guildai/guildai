"""
A tutorial exercise for using different SVM kernels.

Adapted from:
https://scikit-learn.org/stable/auto_examples/exercises/plot_iris_exercise.html
"""

import numpy as np

import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
from sklearn import datasets, svm

kernel = 'linear'  # choice of linear, rbf, poly
test_split = 0.1
random_seed = 0
degree = 3
gamma = 10

iris = datasets.load_iris()
X = iris.data
y = iris.target

X = X[y != 0, :2]
y = y[y != 0]

n_sample = len(X)

np.random.seed(random_seed)
order = np.random.permutation(n_sample)
X = X[order]
y = y[order].astype(np.float)

split_pos = int((1 - test_split) * n_sample)
X_train = X[:split_pos]
y_train = y[:split_pos]
X_test = X[split_pos:]
y_test = y[split_pos:]

# fit the model
clf = svm.SVC(kernel=kernel, degree=degree, gamma=gamma)
clf.fit(X_train, y_train)

print("Train accuracy: %s" % clf.score(X_train, y_train))
print("Test accuracy: %f" % clf.score(X_test, y_test))

plt.figure()
plt.clf()
plt.scatter(X[:, 0], X[:, 1], c=y, zorder=10, cmap=plt.cm.Paired, edgecolor='k', s=20)

# Circle out the test data
plt.scatter(
    X_test[:, 0], X_test[:, 1], s=80, facecolors='none', zorder=10, edgecolor='k'
)

plt.axis('tight')
x_min = X[:, 0].min()
x_max = X[:, 0].max()
y_min = X[:, 1].min()
y_max = X[:, 1].max()

XX, YY = np.mgrid[x_min:x_max:200j, y_min:y_max:200j]
Z = clf.decision_function(np.c_[XX.ravel(), YY.ravel()])

# Put the result into a color plot
Z = Z.reshape(XX.shape)
plt.pcolormesh(XX, YY, Z > 0, cmap=plt.cm.Paired)
plt.contour(
    XX,
    YY,
    Z,
    colors=['k', 'k', 'k'],
    linestyles=['--', '-', '--'],
    levels=[-0.5, 0, 0.5],
)

plt.title(kernel)
plt.savefig("plot.png")

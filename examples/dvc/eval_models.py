# Credit: https://scikit-learn.org/stable/auto_examples/svm/plot_iris_svc.html

import json
import os

import numpy as np
import joblib

import matplotlib.pyplot as plt

from data_util import load_data

if os.path.exists("params.json"):
    params = json.load(open("params.json"))
else:
    params = json.load(open("params.json.in"))

plot_spacing = params["eval"].get("plot-spacing", 0.4)

print("plot_spacing=%f" % plot_spacing)


def make_meshgrid(x, y, h=0.02):
    x_min, x_max = x.min() - 1, x.max() + 1
    y_min, y_max = y.min() - 1, y.max() + 1
    xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))
    return xx, yy


def plot_contours(ax, clf, xx, yy, **params):
    Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)
    out = ax.contourf(xx, yy, Z, **params)
    return out


X, y = load_data()


models = (
    joblib.load("model-1.joblib"),
    joblib.load("model-2.joblib"),
    joblib.load("model-3.joblib"),
    joblib.load("model-4.joblib"),
)

print("Saving models-eval.json")
metrics_data = {
    "modle-1-score": models[0].score(X, y),
    "modle-2-score": models[1].score(X, y),
    "modle-3-score": models[2].score(X, y),
    "modle-4-score": models[3].score(X, y),
}
with open("models-eval.json", "w") as f:
    json.dump(metrics_data, f)

titles = (
    "SVC with linear kernel",
    "LinearSVC (linear kernel)",
    "SVC with RBF kernel",
    "SVC with polynomial (degree 3) kernel",
)

print("Saving models-eval.png")

fig, sub = plt.subplots(2, 2)
plt.subplots_adjust(wspace=plot_spacing, hspace=plot_spacing)

X0, X1 = X[:, 0], X[:, 1]
xx, yy = make_meshgrid(X0, X1)

for clf, title, ax in zip(models, titles, sub.flatten()):
    plot_contours(ax, clf, xx, yy, cmap=plt.cm.coolwarm, alpha=0.8)
    ax.scatter(X0, X1, c=y, cmap=plt.cm.coolwarm, s=20, edgecolors="k")
    ax.set_xlim(xx.min(), xx.max())
    ax.set_ylim(yy.min(), yy.max())
    ax.set_xlabel("Sepal length")
    ax.set_ylabel("Sepal width")
    ax.set_xticks(())
    ax.set_yticks(())
    ax.set_title(title)

plt.savefig("models-eval.png")

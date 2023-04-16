# Credit: https://scikit-learn.org/stable/auto_examples/svm/plot_iris_svc.html

import json
import os

import joblib

from sklearn import svm, datasets

from data_util import load_data

if os.path.exists("params.json"):
    params = json.load(open("params.json"))
else:
    params = json.load(open("params.json.in"))

C = params["train"].get("C", 1.0)
gamma = params["train"].get("gamma", 0.7)
max_iters = params["train"].get("max-iters", 10000)

print("C=%f" % C)
print("gamma=%f" % gamma)
print("max_iters=%f" % max_iters)

models = (
    svm.SVC(kernel="linear", C=C),
    svm.LinearSVC(C=C, max_iter=max_iters),
    svm.SVC(kernel="rbf", gamma=gamma, C=C),
    svm.SVC(kernel="poly", degree=3, gamma="auto", C=C),
)

X, y = load_data()

for i, m in enumerate(models):
    print("Saving model-%i.joblib" % (i + 1))
    m.fit(X, y)
    joblib.dump(m, "model-%i.joblib" % (i + 1))

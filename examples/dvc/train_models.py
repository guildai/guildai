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

C = params["train"]["C"]
print("Using C=%f" % C)

models = (
    svm.SVC(kernel="linear", C=C),
    svm.LinearSVC(C=C, max_iter=10000),
    svm.SVC(kernel="rbf", gamma=0.7, C=C),
    svm.SVC(kernel="poly", degree=3, gamma="auto", C=C),
)


X, y = load_data()


for i, m in enumerate(models):
    print("Saving model-%i.joblib" % (i + 1))
    m.fit(X, y)
    joblib.dump(m, "model-%i.joblib" % (i + 1))

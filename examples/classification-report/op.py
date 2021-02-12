from sklearn.metrics import classification_report

FAKE_STEPS = [
    ([0, 1, 2, 2, 2], [0, 0, 2, 2, 1]),
    ([0, 1, 2, 2, 2], [0, 0, 1, 2, 1]),
    ([0, 1, 2, 2, 2], [0, 1, 2, 2, 0]),
]

target_names = ["class 0", "class 1", "class 2"]

for step, (y_true, y_pred) in enumerate(FAKE_STEPS):
    print("Step %i" % step)
    report = classification_report(y_true, y_pred, target_names=target_names)
    print(report)

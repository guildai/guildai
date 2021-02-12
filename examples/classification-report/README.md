# Classification Report

This example illustrates how Guild can be used to capture output from
scikit-learn's [Classifiction
Report](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html)
as scalar values over a series of steps.

The operation is implemented in [`op.py`](op.py). It prints results
from three simulated training steps using the `classification_report`
function.

The scalars are captured from script output using regular expressions
defined in [`guild.yml`](guild.yml).

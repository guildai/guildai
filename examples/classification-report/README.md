---
doctest-type: bash
---

# Classification Report

This example illustrates how Guild can be used to capture output from
scikit-learn's [Classifiction
Report](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.classification_report.html)
as scalar values over a series of steps.

from three simulated training steps using the `classification_report`
The operation is implemented in [`op.py`](op.py). It prints results
function.

The scalars are captured from script output using regular expressions
defined in [`guild.yml`](guild.yml).

## Run Example

Run the `op` operation:

    $ guild run op -y
    Step 0
                  precision    recall  f1-score   support
    <BLANKLINE>
         class 0       0.50      1.00      0.67         1
         class 1       0.00      0.00      0.00         1
         class 2       1.00      0.67      0.80         3
    <BLANKLINE>
       micro avg       0.60      0.60      0.60         5
       macro avg       0.50      0.56      0.49         5
    weighted avg       0.70      0.60      0.61         5
    <BLANKLINE>
    Step 1
                  precision    recall  f1-score   support
    <BLANKLINE>
         class 0       0.50      1.00      0.67         1
         class 1       0.00      0.00      0.00         1
         class 2       1.00      0.33      0.50         3
    <BLANKLINE>
       micro avg       0.40      0.40      0.40         5
       macro avg       0.50      0.44      0.39         5
    weighted avg       0.70      0.40      0.43         5
    <BLANKLINE>
    Step 2
                  precision    recall  f1-score   support
    <BLANKLINE>
         class 0       0.50      1.00      0.67         1
         class 1       1.00      1.00      1.00         1
         class 2       1.00      0.67      0.80         3
    <BLANKLINE>
       micro avg       0.80      0.80      0.80         5
       macro avg       0.83      0.89      0.82         5
    weighted avg       0.90      0.80      0.81         5
    <exit 0>

The operation prints a series of classification reports.

Guild captures scalars from script output for each of the simulated
steps.

    $ guild compare 1 --table
    run  operation  started  time  status     label  step  f1        prec      recall
    ...  op         ...      ...   completed         2     0.810000  0.899999  0.800000
    <exit 0>

You can run this example as a test using Guild 0.7.3 or later by
running `guild check -t README.md`.

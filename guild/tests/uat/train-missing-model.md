---
doctest: -PY3 +PY37 # 2022-04-11 these tests fail on github actions because TF 1.14 fails to install. We need to update to a more current tensorflow version that has wheels available.
---

# Train missing model

Guild will display an error message if you try to run an operation on
a model it can't find.

    >>> run("guild run -y logreg:train epochs=1")
    guild: cannot find operation logreg:train
    Try 'guild operations' for a list of available operations.
    <exit 1>

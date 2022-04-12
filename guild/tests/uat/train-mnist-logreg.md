---
doctest: -PY3 +PY36 +PY37 # 2022-04-11 these tests fail on github actions because TF 1.14 fails to install. We need to update to a more current tensorflow version that has wheels available.
---

# Train `logreg`

Delete runs in prep for this test.

    >>> quiet("guild runs rm -y")

Train the `logreg` model with one epoch. Note that we don't have to
specify the full model name as long as our term refers to one and only
one model.

    >>> run("guild run -y --no-gpus logreg:train epochs=1")
    Resolving mnist-dataset dependency
    ...
    Step 20:...
    Step 550:...
    ...
    <exit 0>

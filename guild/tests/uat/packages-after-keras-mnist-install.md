---
doctest: -PY3 +PY36 +PY37 # 2022-04-11 on python 3.8+, wheels are not available for h5py<3, so we fail to build. These tests can't currently pass on python 3.8+
---

# Packages after `gpkg.keras.mnist` install

    >>> run("guild packages")
    gpkg.hello           0.7.0...  Sample "hello world" model
    gpkg.keras.mnist     0.7.0...  MNIST models in Keras
    <exit 0>

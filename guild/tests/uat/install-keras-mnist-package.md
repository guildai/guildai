---
doctest: -PY3 +PY36 +PY37 +PY38 # 2022-04-11 on python 3.9+, wheels are not available for h5py<3, so we fail to build. These tests can't currently pass on python 3.9+
---

# Install `gpkg.keras.mnist`

Note that this operation can take a while if required libraries aren't
already installed, so we use longer timeout.

    >>> quiet("guild install gpkg.keras.mnist --pre --no-cache", timeout=120)

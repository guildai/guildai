---
doctest: -PY3 +PY36 +PY37  # 2022-04-11 on python 3.8+, wheels are not available for h5py<3, so we fail to build. These tests can't currently pass on python 3.8+
---

# Install `gpkg.keras.mnist`

    >>> quiet("guild install gpkg.keras.mnist --pre --no-cache")

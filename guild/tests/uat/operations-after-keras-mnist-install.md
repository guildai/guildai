---
doctest: -PY3 +PY36 +PY37  # 2022-04-11 on python 3.8+, wheels are not available for h5py<3, so we fail to build. These tests can't currently pass on python 3.8+
---

# Operations after `gpkg.keras.mnist` install

The `gpkg.keras.mnist` models all provide a single `train` operation.

    >>> run("guild operations keras")
    gpkg.keras.mnist/acgan:train                  Train the model
    gpkg.keras.mnist/cnn:train                    Train the model
    gpkg.keras.mnist/denoising-autoencoder:train  Train the model
    gpkg.keras.mnist/hierarchical-rnn:train       Train the model
    gpkg.keras.mnist/irnn:train                   Train the model
    gpkg.keras.mnist/mlp:train                    Train the model
    gpkg.keras.mnist/net2net:train                Train the model
    gpkg.keras.mnist/siamese:train                Train the model
    <exit 0>

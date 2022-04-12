# Install TensorFlow

    >>> quiet("pip install tensorflow==1.14.0", timeout=120)

    >>> run("guild check --offline --tensorflow")
    guild_version:             ...
    ...
    tensorflow_version:        1.14.0
    tensorflow_cuda_support:   no
    tensorflow_gpu_available:  no
    libcuda_version:           not loaded
    libcudnn_version:          not loaded
    cuda_version:              ...
    ...
    latest_guild_version:      unchecked (offline)
    <exit 0>

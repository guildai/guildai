# Install TensorFlow

We install the version of TensorFlow for our system:

    >>> from guild import util
    >>> if util.gpu_available():
    ...   print("Installing tensorflow-gpu")
    ...   run("pip install tensorflow-gpu")
    ... else:
    ...   print("Installing tensorflow-gpu")
    ...   run("pip install tensorflow")
    Installing tensorflow...
    <exit 0>

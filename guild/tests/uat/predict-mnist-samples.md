# Predict MNIST samples

    >>> run("export samples=`guild runs info | grep run_dir: | cut -d' ' -f2`"
    ...     " && echo Testing softmax serve "
    ...     " && guild serve "
    ...     "    --operation mnist-softmax:train "
    ...     "    --test serving_default "
    ...     "    --test-json-instances $samples/all.json")
    Testing softmax serve
    ...
    Running Guild Serve at http://...
    Testing http://...
    {
      "predictions": [
        {
          "classes": ...,
          "probabilities": [
            ...
          ]
        },
        {
          "classes": ...,
          "probabilities": [
            ...
          ]
        },
        {
          "classes": ...,
          "probabilities": [
            ...
          ]
        },
        {
          "classes": ...,
          "probabilities": [
            ...
          ]
        }
      ]
    }
    <exit 0>

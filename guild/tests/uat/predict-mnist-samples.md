# Predict MNIST samples

    >>> run("export samples=`guild runs info | grep run_dir: | cut -d' ' -f2`"
    ...     " && echo Testing serve "
    ...     " && CUDA_VISIBLE_DEVICES= guild serve "
    ...     "    --operation logreg:train "
    ...     "    --test serving_default "
    ...     "    --test-json-instances $samples/all.json")
    Testing serve
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

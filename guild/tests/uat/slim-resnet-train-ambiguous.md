# slim.resnet train ambiguous

We have a number of resnet models:

    >>> run("guild models resnet")
    slim.resnet/slim-resnet-101     ResNet-101 classifier for TF-Slim
    slim.resnet/slim-resnet-152     ResNet-152 classifier for TF-Slim
    slim.resnet/slim-resnet-200     ResNet-200 classifier for TF-Slim
    slim.resnet/slim-resnet-50      ResNet-50 classifier for TF-Slim
    slim.resnet/slim-resnet-v2-101  ResNet-v2-101 classifier for TF-Slim
    slim.resnet/slim-resnet-v2-152  ResNet-v2-152 classifier for TF-Slim
    slim.resnet/slim-resnet-v2-200  ResNet-v2-200 classifier for TF-Slim
    slim.resnet/slim-resnet-v2-50   ResNet-v2-50 classifier for TF-Slim
    <exit 0>

If we try to train using an ambiguous model, we get an error:

    >>> run("guild train resnet dataset=flowers -y")
    guild: there are multiple models that match 'resnet'
    Try specifying one of the following:
      slim.resnet/slim-resnet-101
      slim.resnet/slim-resnet-152
      slim.resnet/slim-resnet-200
      slim.resnet/slim-resnet-50
      slim.resnet/slim-resnet-v2-101
      slim.resnet/slim-resnet-v2-152
      slim.resnet/slim-resnet-v2-200
      slim.resnet/slim-resnet-v2-50
    <exit 1>

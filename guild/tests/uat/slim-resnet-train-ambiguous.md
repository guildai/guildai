# slim.resnet train ambiguous

We have a number of resnet models:

TODO: reinstate after 0.5 slim packages are finalized

    >> run("guild models resnet")
    gpkg.slim.resnet/slim-resnet-101     ResNet-101 classifier for TF-Slim
    gpkg.slim.resnet/slim-resnet-152     ResNet-152 classifier for TF-Slim
    gpkg.slim.resnet/slim-resnet-200     ResNet-200 classifier for TF-Slim
    gpkg.slim.resnet/slim-resnet-50      ResNet-50 classifier for TF-Slim
    gpkg.slim.resnet/slim-resnet-v2-101  ResNet-v2-101 classifier for TF-Slim
    gpkg.slim.resnet/slim-resnet-v2-152  ResNet-v2-152 classifier for TF-Slim
    gpkg.slim.resnet/slim-resnet-v2-200  ResNet-v2-200 classifier for TF-Slim
    gpkg.slim.resnet/slim-resnet-v2-50   ResNet-v2-50 classifier for TF-Slim
    <exit 0>

If we try to train using an ambiguous model, we get an error:

TODO: reinstate after 0.5 slim packages are finalized

    >> run("guild run resnet:train dataset=flowers -y")
    guild: there are multiple models that match 'resnet'
    Try specifying one of the following:
      gpkg.slim.resnet/slim-resnet-101
      gpkg.slim.resnet/slim-resnet-152
      gpkg.slim.resnet/slim-resnet-200
      gpkg.slim.resnet/slim-resnet-50
      gpkg.slim.resnet/slim-resnet-v2-101
      gpkg.slim.resnet/slim-resnet-v2-152
      gpkg.slim.resnet/slim-resnet-v2-200
      gpkg.slim.resnet/slim-resnet-v2-50
    <exit 1>

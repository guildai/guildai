#-*-python-*-

workspace(name = "org_guildai_guild")

http_archive(
    name = "io_bazel_rules_closure",
    sha256 = "2b43d9b683ba8c34811b31cc4afebbce3cf3beae528fc678bb37e23054942b8a",
    strip_prefix = "rules_closure-4c559574447f90751f05155faba4f3344668f666",
    urls = [
        "https://github.com/bazelbuild/rules_closure/archive/4c559574447f90751f05155faba4f3344668f666.tar.gz",  # 2017-06-21
    ],
)

load("@io_bazel_rules_closure//closure:defs.bzl", "closure_repositories")

closure_repositories()

http_archive(
    name = "org_tensorflow_tensorboard",
    sha256 = "01882d640f205e4872da04d127e2014cfb342097eb1c22bc52af8bbb53e0d06b",
    strip_prefix = "tensorboard-2da8a6d6b79b29b192dac8d227ab82ad3479b1fc",
    urls = [
        "https://github.com/tensorflow/tensorboard/archive/2da8a6d6b79b29b192dac8d227ab82ad3479b1fc.tar.gz",
    ],
)

load("//third-party:workspace.bzl", "third_party_workspace")

third_party_workspace()

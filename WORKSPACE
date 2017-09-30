#-*-python-*-

workspace(name = "org_guildai_guild")

http_archive(
    name = "io_bazel_rules_closure",
    sha256 = "f73b1b3974e7639183e1646737d446d73a966ff57f853a896e19bcccc40e9b7b",
    strip_prefix = "rules_closure-4af89ef1db659eb41f110df189b67d4cf14073e1",
    urls = [
        "https://github.com/bazelbuild/rules_closure/archive/4af89ef1db659eb41f110df189b67d4cf14073e1.zip",
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

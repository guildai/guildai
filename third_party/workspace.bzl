load("@org_tensorflow_tensorboard//third_party:workspace.bzl", "tensorboard_workspace")
load("//third_party:python.bzl", "guild_python_workspace")

def third_party_workspace():
    tensorboard_workspace()
    guild_python_workspace()

import os

from guild import summary

attrs = summary.SummaryWriter(".", filename_suffix=".attrs")
summaries = summary.SummaryWriter(".")

attrs.add_text("model", "cnn")
attrs.add_text("id", "abcd1234")

summaries.add_scalar("loss", 0.123, step=1)
summaries.add_scalar("loss", 0.1, step=2)
summaries.add_scalar("loss", 0.06, step=3)
summaries.add_scalar("loss", 0.01, step=4)

os.mkdir("train")
train_attrs = summary.SummaryWriter("train", filename_suffix=".attrs")
train_summaries = summary.SummaryWriter("train")

train_attrs.add_text("model", "cnn-2")

train_summaries.add_scalar("loss", 0.223, step=1)
train_summaries.add_scalar("loss", 0.2, step=2)
train_summaries.add_scalar("loss", 0.08, step=3)
train_summaries.add_scalar("loss", 0.03, step=4)

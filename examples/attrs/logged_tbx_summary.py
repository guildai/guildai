import tensorboardX as tbx

attrs = tbx.SummaryWriter(".", filename_suffix=".attrs")
summaries = tbx.SummaryWriter(".")

attrs.add_text("model", "cnn")

summaries.add_scalar("loss", 0.123, global_step=1)
summaries.add_scalar("loss", 0.1, global_step=2)
summaries.add_scalar("loss", 0.06, global_step=3)
summaries.add_scalar("loss", 0.01, global_step=4)

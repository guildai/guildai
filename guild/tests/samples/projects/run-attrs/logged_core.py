from guild import summary

attrs = summary.SummaryWriter(".", filename_suffix=".attrs")
attrs.add_text("id", "bbb")
attrs.add_text("label", "Trying to log a label")

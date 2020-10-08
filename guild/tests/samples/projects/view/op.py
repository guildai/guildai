from guild import summary

with summary.SummaryWriter(".") as writer:
    writer.add_scalar("x", 1.123, step=1)
    writer.add_scalar("x", 2.234, step=2)
    writer.add_scalar("x", float("inf"), step=3)
    writer.add_scalar("y", float("-inf"), step=1)
    writer.add_scalar("y", 1, step=2)
    writer.add_scalar("y", 2, step=3)
    writer.add_scalar("z", float("nan"), step=1)

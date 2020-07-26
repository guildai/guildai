import tensorboardX

with tensorboardX.SummaryWriter("foo") as w:
    w.add_scalar("a", 1.0, 1)
    w.add_scalar("a", 2.0, 2)


with tensorboardX.SummaryWriter("foo/bar") as w:
    w.add_scalar("a", 3.0, 3)
    w.add_scalar("a", 4.0, 4)

with tensorboardX.SummaryWriter("foo/bar/baz") as w:
    w.add_scalar("a", 5.0, 5)
    w.add_scalar("a", 6.0, 6)

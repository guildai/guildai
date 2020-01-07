import numpy as np

from guild import summary

noise = 0.1


def f(x):
    return np.sin(5 * x) * (1 - np.tanh(x ** 2)) + np.random.randn() * noise


min_loss = None
writer = summary.SummaryWriter(".")

for step, x in enumerate(np.arange(-3.0, 3.0, 0.1)):
    loss = f(x)
    min_loss = min(loss, min_loss) if min_loss is not None else loss
    writer.add_scalar("loss", loss, step)

writer.close()
print("min_loss: %f" % min_loss)

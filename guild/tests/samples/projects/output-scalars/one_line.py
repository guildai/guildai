steps = 10

_loss = 5.0
_acc = 0.1

for step in range(steps):
    print("Step {}: loss={} acc={}".format(step, _loss, _acc))
    _loss -= 0.1
    _acc += 0.1

steps = 10

_loss = 5.0
_acc = 0.1

for step in range(steps):
    print("Step {}:".format(step))
    print("  loss: {}".format(_loss))
    print("  acc: {}".format(_acc))
    print("")
    _loss -= 0.1
    _acc += 0.1

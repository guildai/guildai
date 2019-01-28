import random

lr = 0.1
print("params:")
print(" lr=%f" % lr)

loss = random.uniform(0, lr) * 100
print("loss: %f" % loss)

print("Saving model as ./trained-model")
open("trained-model", "w").close()

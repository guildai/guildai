layers = 1

model = "cnn" if layers < 2 else "deep-cnn"

print(f"model: {model}")
print("loss: 0.123")
print("acc: 0.654")

import sys

# Set scalar step using "step: N"
print("step: 1")

# Log scalars in the format 'KEY: VALUE'
print("loss: 2.345")
print("accuracy: 0.123")
print("")

# Setting step again applies to subsequently logged scalars
print("step: 2")

# Step 2 scalar vals
print("loss: 1.234")
print("accuracy: 0.456")
print("")

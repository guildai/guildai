# step is logged using the two supported forms: with and without the step term

print("x: 1 (step 1)")
print("x: 3 (3)")           # intentionally out of order
print("x: 2 (step 2)")
print("x: 4")               # logged as step 2 (last-logged)
print("x: 5 (5)")
print("x: 6 (not a step)")  # still captured but not with step

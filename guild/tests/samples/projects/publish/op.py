a = 1
b = 2

print("x: %i" % (a + b))
print("y: %i" % (b - a))

open("generated-1.txt", "wb").write(b"Hola\n")
open("generated-2.txt", "wb").write(b"Yo yo yo\n")

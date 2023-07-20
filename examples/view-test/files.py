count = 20

print(f"Generating {count} file(s)")

for i in range(count):
    with open(f"output-{i+1}", "w") as f:
        f.write(f"Generated file {i+1}\n")

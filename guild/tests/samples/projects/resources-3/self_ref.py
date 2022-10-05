try:
    open("file")
except FileNotFoundError:
    print("file not found - creating")
    open("file", "w").close()
else:
    print("file found")

import os

exists = os.path.exists("generated")
is_link = os.path.islink("generated")

print(f"generated: exists={exists} islink={is_link}")

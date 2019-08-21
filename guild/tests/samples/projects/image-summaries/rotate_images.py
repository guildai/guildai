from PIL import Image

img = Image.open("favicon.png")
for x in (0, 90, 180, 270):
    img.rotate(x).save("favicon-%s.png" % x)

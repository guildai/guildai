import os

from PIL import Image

for name in os.listdir("."):
    base, ext = os.path.splitext(name)
    try:
        img = Image.open(name)
    except IOError as e:
        pass
    else:
        for x in (0, 90, 180, 270):
            img.rotate(x).save("%s-%i%s" % (base, x, ext))

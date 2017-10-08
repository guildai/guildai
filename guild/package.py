class Package(object):

    def __init__(self, name, version):
        self.name = name
        self.version = version

    def __cmp__(self, x):
        if isinstance(x, Package):
            # TODO: implement actual version sorting
            return cmp((self.name, self.version), (x.name, x.version))
        else:
            return -1

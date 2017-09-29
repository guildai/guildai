import uuid

class Run(object):

    def __init__(self, id, path):
        self.id = id
        self.path = path

def init_run():
    id = uuid.uuid1()
    path = os.path.join(guild.var.path("runs"), id)
    return Run(id, path)

GUILD_PACKAGE_NAMESPACE = "gpkg"

def guild_to_python(name):
    return (name[1:] if name[0] == "!"
            else GUILD_PACKAGE_NAMESPACE + "." + name)

import configparser
import io

flags = configparser.ConfigParser()
flags.read("flags.ini")

out = io.StringIO()
flags.write(out)
print(out.getvalue())

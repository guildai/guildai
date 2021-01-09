import configparser
import pprint
import sys


src = sys.argv[1]
config = configparser.ConfigParser()
config.read(src)
config.write(sys.stdout)

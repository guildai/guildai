import logging

import guild.log
import guild.namespace
import guild.plugin

def main(args):
    guild.log.init_logging(args.log_level or logging.INFO)
    guild.namespace.init_namespaces()
    guild.plugin.init_plugins()

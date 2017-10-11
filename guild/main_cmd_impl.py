import logging

import guild.log
import guild.plugin

def main(args):
    guild.log.init_logging(args.log_level or logging.INFO)
    guild.plugin.init_plugins()

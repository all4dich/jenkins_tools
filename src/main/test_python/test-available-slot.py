import logging
import re
from datetime import datetime
# import pymongo

from multiprocessing import Pool, Manager

from jenkins_tools.common import Jenkins
import argparse

COMMAND_LAUNCHER = "hudson.slaves.CommandLauncher"
SSH_LAUNCHER = "hudson.plugins.sshslaves.SSHLauncher"

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--url", required=True)
arg_parser.add_argument("--username", required=True)
arg_parser.add_argument("--password", required=True)
args = arg_parser.parse_args()
url = args.url
username = args.username
password = args.password

# Set Log Level
loglevel = "INFO"
numeric_level = getattr(logging, loglevel.upper(), None)
log_console_format = "[%(levelname)s] %(asctime)s - %(name)s - %(message)s (in %(pathname)s:%(lineno)d)"
logging.basicConfig(format=log_console_format, datefmt="%m/%d/%Y %I:%M:%S %p %Z")
logging.getLogger().setLevel(numeric_level)

j = Jenkins(url, username, password)
if j.check_connection():
    logging.info("Success")
else:
    logging.error("Fail")


j.check_slot_available("wish")
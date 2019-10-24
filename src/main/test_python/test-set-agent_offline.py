import logging
import re
from datetime import datetime
import pymongo

logger = logging.getLogger()

from jenkins_tools.common import Jenkins
from jenkins_tools.types import JobClasses
import jenkins_tools.types as types
url = input("Jenkins Url: ")
username = "allessunjoo.park"
password = input(f"Password for {username} ")
j = Jenkins(url, username, password)
if j.check_connection():
    logger.info("Success")
else:
    logger.error("Fail")

print(j.set_agent_offline("swfarm-gateuobld03"))

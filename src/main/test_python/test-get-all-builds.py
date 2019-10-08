import logging
import re
from datetime import datetime
import pymongo

logger = logging.getLogger()

from jenkins_tools.common import Jenkins
from jenkins_tools.types import JobClasses
import jenkins_tools.types as types
url = "http://localhost:7070/"
username = "admin"
password = "admin"
j = Jenkins(url, username, password)
if j.check_connection():
    logger.info("Success")
else:
    logger.error("Fail")
logger.info(datetime.now())
logger.info("start")
logger.info("end")
logger.info(datetime.now())

r = j.get_job_builds("test1")
print("end")

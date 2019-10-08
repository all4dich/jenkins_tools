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
password = "1184594d8f69c5f3b7670f34c29b2c54a3"
j = Jenkins(url, username, password)
if j.check_connection():
    logger.info("Success")
else:
    logger.error("Fail")
logger.info(datetime.now())
logger.info("start")
logger.info("end")
logger.info(datetime.now())

job_name = "test1"
r = j.get_job_builds(job_name)
for build in r:
    print(f"Delete {job_name} #{build['number']}")
    j.delete_build(job_name, build['number'])
print("end")

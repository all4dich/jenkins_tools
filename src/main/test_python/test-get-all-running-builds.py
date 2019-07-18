import logging
import re
from datetime import datetime
import pymongo

logger = logging.getLogger()

from jenkins_tools.common import Jenkins
from jenkins_tools.types import JobClasses
import jenkins_tools.types as types

j = Jenkins("http://localhost:7070", "admin", "admin")
if j.check_connection():
    logger.info("Success")
else:
    logger.error("Fail")
logger.info(datetime.now())
logger.info("start")
logger.info("end")
logger.info(datetime.now())

full_url = f"{j.url}/computer/api/json?pretty=true&tree=computer[displayName,executors[idle,number,currentExecutable[fullDisplayName]]]"
agents = j.get_object(url=full_url, api_suffix="")['computer']
running_builds = []
idle_executors = []
for each_agent in agents:
    agent_name = each_agent['displayName']
    executors = each_agent['executors']
    for each_executor in executors:
        idle = each_executor['idle']
        if idle == False:
            running_builds.append({
                "agent": agent_name,
                "number": each_executor['number'],
                "build": each_executor['currentExecutable']['fullDisplayName']
            })
        else:
            idle_executors.append(each_executor)

for each_build in running_builds:
    print(each_build)
print(len(running_builds))
print(idle_executors)

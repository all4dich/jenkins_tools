import logging
from datetime import datetime
import argparse
import pandas as pd

logging.getLogger().setLevel("ERROR")
from jenkins_tools.common import Jenkins
from jenkins_tools.types import JobClasses
import jenkins_tools.types as types

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--url", required=True)
arg_parser.add_argument("--username", required=True)
arg_parser.add_argument("--password", required=True)
args = arg_parser.parse_args()
jenkins_url = args.url
username = args.username
password = args.password
j = Jenkins(jenkins_url, username, password)
if j.check_connection():
    logging.info("Success")
else:
    logging.error("Fail")
logging.info(datetime.now())
logging.info("start")
logging.info("end")
logging.info(datetime.now())

full_url = f"{j.url}/computer/api/json?pretty=true&tree=computer[displayName,idle,offline,numExecutors," \
           f"executors[idle,number,currentExecutable[fullDisplayName]]]"
agents = j.get_object(url=full_url, api_suffix="")['computer']
running_builds = []
idle_executors = []
idle_hosts = []
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
            idle_executors.append([agent_name, each_executor])
            idle_hosts.append(agent_name)

for each_build in running_builds:
    print(each_build['build'], each_build['agent'])
idle_hosts = sorted(set(idle_hosts))
for each_agent in idle_hosts:
    print(each_agent)

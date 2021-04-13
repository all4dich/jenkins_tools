import logging
import argparse
from datetime import datetime
import re

logging.getLogger().setLevel("ERROR")
from jenkins_tools.common import Jenkins

# https://cerberus.lge.com/jenkins/computer/api/json?pretty=true&tree=computer[displayName,idle,offline,numExecutors,executors[idle,number,currentExecutable[fullDisplayName,number,url]]]
if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--url", required=True)
    arg_parser.add_argument("--username", required=True)
    arg_parser.add_argument("--password", required=True)
    args = arg_parser.parse_args()
    jenkins_url = args.url
    username = args.username
    password = args.password
    j = Jenkins(jenkins_url, username, password)
    start = datetime.now().astimezone()
    running_builds = j.get_running_builds()["running_builds"]
    for each_build in running_builds:
        build_name = each_build['build_name'].split(" #")
        build_url = each_build['build_url']
        build_job = build_name[0]
        build_number = build_name[1]
        if re.compile(r"(starfish|clean).*").match(build_job):
            print(build_job)
            r = j.get_build_parameters(build_job, build_number)
            print(r)
    end = datetime.now().astimezone()
    print(f"Time to complete: {end-start}")
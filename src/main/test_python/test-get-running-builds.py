import logging
import argparse

logging.getLogger().setLevel("ERROR")
from jenkins_tools.common import Jenkins

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
    running_builds = j.get_running_builds()
    for each_build in running_builds:
        print(each_build['build'], each_build['agent'])

import logging
import argparse
from datetime import datetime
import re

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
    start = datetime.now().astimezone()
    running_builds = j.get_running_builds()["running_builds"]
    for each_build in running_builds:
        build_name = each_build['build_name'].split(" #")
        build_url = each_build['build_url']
        build_job = build_name[0]
        build_number = build_name[1]
        # Common fields
        #  - BRANCH, PROJECT, OWNER, BUILD_TYPE, CHIP, HOST
        if re.compile(r"starfish-.*-(verify|integrate)-.*").match(build_job):
            params = j.get_build_parameters(build_job, build_number)
            git_branch = params['GERRIT_BRANCH']
            git_project = params['GERRIT_PROJECT']
            change_owner = params['GERRIT_CHANGE_OWNER_NAME']
            change_owner_email = params['GERRIT_CHANGE_OWNER_EMAIL']
            build_type = build_job.split("-")[2]
            chip_name = build_job.split("-")[-1]
            print(build_name, git_branch, change_owner)
        elif re.compile(r"starfish-.*-official-.*").match(build_job):
            r_official = j.get_git_build_data(build_job, build_number)
            git_branch = r_official['branch_name']
            build_user = r_official['requestor']
            print(build_name, git_branch, build_user)
        elif re.compile(r"clean-engineering-starfish-.*-build").match(build_job):
            r = j.get_build_parameters(build_job, build_number)

    end = datetime.now().astimezone()
    print(f"Time to complete: {end - start}")

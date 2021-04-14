import logging
import argparse
from datetime import datetime
import re
import pandas as pd

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
    output_table_header = ["Job", "Build Number", "Branch", "Owner", "Builjd Url"]
    output_table = []

    for each_build in running_builds:
        build_name_str = each_build['build_name']
        build_name = build_name_str.split(" #")
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
            output_table.append([build_job, build_number, git_branch, change_owner, build_url])
        elif re.compile(r"starfish-.*-official-.*").match(build_job):
            r_official = j.get_git_build_data(build_job, build_number)
            git_branch = r_official['branch_name']
            build_user = r_official['requestor']
            output_table.append([build_job, build_number, git_branch, change_owner, build_url])
        elif re.compile(r"clean-engineering-starfish-.*-build").match(build_job):
            params = j.get_build_parameters(build_job, build_number)
            if 'GERRIT_BRANCH' in params.keys():
                git_branch = params['GERRIT_BRANCH']
                change_owner = params['GERRIT_CHANGE_OWNER_NAME']
            else:
                build_causes = j.get_build_causes(build_job, build_number)
                change_owner = []
                for each_cause in build_causes:
                    if each_cause['_class'] == 'hudson.model.Cause$UpstreamCause':
                        upstream_project = each_cause['upstreamProject']
                        upstream_build_number = each_cause['upstreamBuild']
                    elif each_cause['_class'] == "hudson.model.Cause$UserIdCause":
                        change_owner.append(each_cause['userName'])
                if upstream_project and upstream_build_number:
                    upstream_causes = j.get_build_causes(upstream_project, upstream_build_number)
                    for upstream_cause in upstream_causes:
                        if upstream_cause['_class'] == "hudson.model.Cause$UserIdCause":
                            change_owner.append(upstream_cause['userName'])
                    git_branch = params['build_starfish_commit']
                else:
                    git_branch = "clean-build"
                    change_owner = "clean-build"
                change_owner = ",".join(change_owner)
            output_table.append([build_job, build_number, git_branch, change_owner, build_url])
    df = pd.DataFrame(data=output_table, columns=output_table_header)
    df2 = df.style.set_properties(**{'text-align': 'left'})
    print(df.to_string())
    end = datetime.now().astimezone()
    print(f"Time to complete: {end - start}")

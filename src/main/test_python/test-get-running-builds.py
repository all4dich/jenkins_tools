import logging
import argparse
from datetime import datetime
import re
import pandas as pd
from multiprocessing import Pool
from functools import partial

logging.getLogger().setLevel("ERROR")
from jenkins_tools.common import Jenkins

from pymongo import MongoClient


def get_build_info(jenkins_url, username, password, each_build):
    j = Jenkins(jenkins_url, username, password)
    build_name_str = each_build['build_name']
    build_name = build_name_str.split(" #")
    build_url = each_build['build_url']
    build_job = build_name[0]
    build_number = build_name[1]
    # Common fields
    #  - BRANCH, PROJECT, OWNER, BUILD_TYPE, CHIP, HOST
    #  - Build job, Build Number, Chip, Type, Branch, Owner, Url
    output = []
    if re.compile(r"starfish-.*-(verify|integrate)-.*").match(build_job):
        params = j.get_build_parameters(build_job, build_number)
        git_branch = params['GERRIT_BRANCH']
        git_project = params['GERRIT_PROJECT']
        change_owner = params['GERRIT_CHANGE_OWNER_NAME']
        change_owner_email = params['GERRIT_CHANGE_OWNER_EMAIL']
        build_type = build_job.split("-")[2]
        chip_name = build_job.split("-")[-1]
        output = [build_job, build_number, chip_name, build_type, git_branch, change_owner, build_url]
    elif re.compile(r"starfish-.*-official-.*").match(build_job):
        r_official = j.get_git_build_data(build_job, build_number)
        git_branch = r_official['branch_name']
        change_owner = r_official['requestor']
        build_type = build_job.split("-")[2]
        chip_name = build_job.split("-")[-1]
        output = [build_job, build_number, chip_name, build_type, git_branch, change_owner, build_url]
    elif re.compile(r"clean-engineering-starfish-.*-build").match(build_job):
        params = j.get_build_parameters(build_job, build_number)
        build_type = build_job.split("-")[0]
        chip_name = build_job.split("-")[-2]
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
        output = [build_job, build_number, chip_name, build_type, git_branch, change_owner, build_url]
    else:
        output = [build_job, build_number, "", "", "", "", build_url]
    return output


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--url", required=True)
    arg_parser.add_argument("--username", required=True)
    arg_parser.add_argument("--password", required=True)
    arg_parser.add_argument("--dbhost", required=True)
    arg_parser.add_argument("--dbport", required=True)
    arg_parser.add_argument("--dbname", required=True)
    arg_parser.add_argument("--dbcollection", required=True)
    arg_parser.add_argument("--dbusername", required=True)
    arg_parser.add_argument("--dbpassword", required=True)
    args = arg_parser.parse_args()
    jenkins_url = args.url
    username = args.username
    password = args.password
    jenkins_connector = Jenkins(jenkins_url, username, password)
    start = datetime.now().astimezone()
    running_builds = jenkins_connector.get_running_builds()["running_builds"]
    output_table_header = ["Job", "Build Number", "Chip", "Type", "Branch", "Owner", "Build Url"]
    p = Pool()
    db_client = MongoClient(host=args.dbhost, port=int(args.dbport), username=args.dbusername, password=args.dbpassword,
                            authSource=args.dbname)
    db = db_client[args.dbname]
    db_collection = db[args.dbcollection]
    output_table = p.map(partial(get_build_info, jenkins_url, username, password), running_builds)
    for each_build in output_table:
        db_collection.insert_one({
            "job": each_build[0],
            "number": each_build[1],
            "chip": each_build[2],
            "type": each_build[3],
            "branch": each_build[4],
            "owner": each_build[5],
            "url": each_build[6],
            "time": start,
            "time_epoch": start.timestamp(),
            "zone": start.tzname()
        })
    df = pd.DataFrame(data=output_table, columns=output_table_header)
    df2 = df.style.set_properties(**{'text-align': 'left'})
    print(df.to_string())
    end = datetime.now().astimezone()
    print(f"Time to complete: {end - start}")
    print(start)

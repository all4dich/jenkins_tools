import logging
import argparse
from datetime import datetime
import re
from multiprocessing import Pool
from functools import partial

logging.getLogger().setLevel("ERROR")
from jenkins_tools.common import Jenkins


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--url", required=True)
    arg_parser.add_argument("--username", required=True)
    arg_parser.add_argument("--password", required=True)
    arg_parser.add_argument("--dbhost", required=True)
    arg_parser.add_argument("--dbport", required=True)
    arg_parser.add_argument("--dbname", required=True)
    arg_parser.add_argument("--dbtable", required=True)
    arg_parser.add_argument("--dbusername", required=True)
    arg_parser.add_argument("--dbpassword", required=True)
    args = arg_parser.parse_args()
    jenkins_url = args.url
    username = args.username
    password = args.password
    print("\n\n\n")
    jenkins_connector = Jenkins(jenkins_url, username, password)
    start = datetime.now().astimezone()
    r = jenkins_connector.get_in_queue_builds()
    end= datetime.now().astimezone()
    print(end-start)

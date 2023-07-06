import logging
import argparse
from datetime import datetime
import re
from multiprocessing import Pool
from functools import partial
import requests

logging.getLogger().setLevel("ERROR")
from jenkins_tools.common import Jenkins
import mysql.connector




if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--url", required=True)
    arg_parser.add_argument("--username", required=True)
    arg_parser.add_argument("--password", required=True)
    args = arg_parser.parse_args()
    jenkins_url = args.url
    username = args.username
    password = args.password
    print("\n\n\n")
    jenkins_connector = Jenkins(jenkins_url, username, password)
    current_time = datetime.now().astimezone()
    queued_items = jenkins_connector.get_in_queue_builds()
    i = 1
    for each_item in queued_items:
        item_class = each_item["_class"].replace("$", "_")
        item_id = each_item["id"]
        item_since = each_item["inQueueSince"] / 1000
        item_task = each_item["task"]
        item_url = each_item["url"]
        job_name = item_task["name"]
        item_url_url = jenkins_url + item_url
        cancel_url = f"{jenkins_url}queue/cancelItem?id={item_id}"
        cancel_request = requests.post(cancel_url, auth=(username,password))
        print(job_name, item_id, cancel_request.status_code)
    end = datetime.now().astimezone()
    print("INFO:", "Elapsed time = ", end - current_time)
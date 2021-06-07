import logging
import argparse
from datetime import datetime
import re
from multiprocessing import Pool
from functools import partial

logging.getLogger().setLevel("ERROR")
from jenkins_tools.common import Jenkins
import mysql.connector


def get_in_queue_info_table_description(table_name):
    table_description = f"CREATE TABLE `{table_name}` (" \
                        "  `job` VARCHAR(200) NOT NULL," \
                        "  `job_class` VARCHAR(200) NOT NULL," \
                        "  `job_url` VARCHAR(200) NOT NULL," \
                        "  `why` VARCHAR(200) NOT NULL," \
                        "  `url` VARCHAR(200) NOT NULL," \
                        "  `since_timestamp` TIMESTAMP NOT NULL," \
                        "  `since` INT(4)," \
                        "  `current` INT(4)," \
                        "  `inqueue` INT(4)" \
                        ")"
    return table_description


def get_table_insert_description(table_name):
    insert_description = f"INSERT INTO {table_name} (" \
                         "  job, " \
                         "  job_class, " \
                         "  job_url, " \
                         "  why, " \
                         "  url, " \
                         "  since_timestamp, since, current, inqueue ) VALUES  (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
    return insert_description


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
    queued_items = jenkins_connector.get_in_queue_builds()
    cnx = mysql.connector.connect(user=args.dbusername,
                                  password=args.dbpassword,
                                  host=args.dbhost,
                                  port=int(args.dbport)
                                  )
    cursor = cnx.cursor()
    try:
        cursor.execute(f"CREATE DATABASE {args.dbname} DEFAULT CHARACTER SET 'utf8'")
    except mysql.connector.Error as err:
        error_number = err.errno
        if error_number == 1007:
            print(f"INFO: Database {args.dbname} exists")
        else:
            print(err)
            exit(1)
    try:
        cursor.execute(f"Use {args.dbname}")
        # Create a table
        create_table_description = get_in_queue_info_table_description(args.dbtable)
        cursor.execute(create_table_description)
    except mysql.connector.Error as err:
        error_number = err.errno
        print(err)
        if error_number != 1050:
            print("ERROR: Terminated, Can't create the table")
            exit(1)
        else:
            print("INFO: Continue with the existing table ")
    try:
        for each_item in queued_items:
            item_class = each_item["_class"].replace("$", "_")
            item_id = each_item["id"]
            item_since = each_item["inQueueSince"] / 1000
            item_task = each_item["task"]
            try:
                job_name = item_task["name"]
            except:
                job_name = "N/A"
            job_url = item_task["url"]
            job_class = item_task["_class"]
            item_url = each_item["url"]
            item_full_url = jenkins_connector.url + "/" + item_url
            item_reason = each_item["why"]
            curr_timestamp = int(start.timestamp())
            in_queue_time = int(curr_timestamp - item_since)
            item_since_in_seconds = int(item_since)
            item_since_datetime = datetime.fromtimestamp(item_since).astimezone()
            query_data = (
                job_name, item_class, job_url, item_reason, item_url, item_since_datetime, item_since_in_seconds, curr_timestamp, in_queue_time)
            cursor.execute(get_table_insert_description(args.dbtable), query_data)
    except mysql.connector.errors.ProgrammingError as err:
        print(err)
    finally:
        cnx.commit()
        cnx.close()
    end = datetime.now().astimezone()
    print(end - start)
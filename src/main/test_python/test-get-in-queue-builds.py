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
                        "  `job_type` VARCHAR(200) NOT NULL," \
                        "  `job_branch` VARCHAR(200) NOT NULL," \
                        "  `job_chip` VARCHAR(200) NOT NULL," \
                        "  `job_distro` VARCHAR(200) NOT NULL," \
                        "  `job_class` VARCHAR(200) NOT NULL," \
                        "  `job_url` VARCHAR(200) NOT NULL," \
                        "  `why` VARCHAR(200) NOT NULL," \
                        "  `url` VARCHAR(200) NOT NULL," \
                        "  `since_date` DATETIME NOT NULL," \
                        "  `since_timestamp` INT(4)," \
                        "  `curr_date` DATETIME NOT NULL," \
                        "  `curr_timestamp` INT(4)," \
                        "  `inqueue` INT(4)" \
                        ")"
    return table_description


def get_table_insert_description(table_name):
    insert_description = f"INSERT INTO {table_name} (" \
                         "  job, " \
                         "  job_type, " \
                         "  job_branch, " \
                         "  job_chip, " \
                         "  job_distro, " \
                         "  job_class, " \
                         "  job_url, " \
                         "  why, " \
                         "  url, " \
                         "  since_date, since_timestamp, curr_date, curr_timestamp, inqueue ) VALUES  (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
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
    current_time = datetime.now().astimezone()
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
            job_name_elements = job_name.split("-")
            job_branch = "others"
            job_type = "others"
            job_chip = "others"
            job_distro = "others"
            if job_name_elements[0] == "starfish":
                if len(job_name_elements) > 3:
                    job_chip = job_name_elements[3]
                    job_type = job_name_elements[2]
                    job_branch = job_name_elements[1]
                    job_distro = job_name_elements[0]
                else:
                    job_type = "others"
            elif job_name_elements[0] == "clean":
                job_chip = "clean"
                job_type = "clean"
                job_branch = "clean"
                if len(job_name_elements) == 5:
                    job_chip = job_name_elements[3]
                    job_distro = job_name_elements[2]
            job_url = item_task["url"]
            job_class = item_task["_class"]
            item_url = each_item["url"]
            item_full_url = jenkins_connector.url + "/" + item_url
            item_reason = each_item["why"]
            curr_timestamp = int(current_time.timestamp())
            in_queue_time = int(curr_timestamp - item_since)
            item_since_in_seconds = int(item_since)
            item_since_datetime = datetime.fromtimestamp(item_since).astimezone()
            query_data = (
                job_name, job_type, job_branch, job_chip, job_distro, item_class, job_url, item_reason, item_url, 
                item_since_datetime, item_since_in_seconds, 
                current_time, curr_timestamp, 
                in_queue_time)
            cursor.execute(get_table_insert_description(args.dbtable), query_data)
    except mysql.connector.errors.ProgrammingError as err:
        print(f"ERROR: {err}")
    finally:
        cnx.commit()
        cnx.close()
    end = datetime.now().astimezone()
    print("INFO:", "Elapsed time = ", end - current_time)
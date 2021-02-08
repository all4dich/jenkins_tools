import logging
import re
from datetime import datetime
# import pymongo

from multiprocessing import Pool, Manager

from jenkins_tools.common import Jenkins
import argparse
from lxml import etree
import pandas as pd
from paramiko import SSHClient, AutoAddPolicy

logger = logging.getLogger()
COMMAND_LAUNCHER = "hudson.slaves.CommandLauncher"
SSH_LAUNCHER = "hudson.plugins.sshslaves.SSHLauncher"

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("--url", required=True)
arg_parser.add_argument("--username", required=True)
arg_parser.add_argument("--password", required=True)
arg_parser.add_argument("--list-output", help="Excel file")

args = arg_parser.parse_args()
url = args.url
username = args.username
password = args.password

j = Jenkins(url, username, password)
if j.check_connection():
    logger.info("Success")
else:
    logger.error("Fail")


def get_agents():
    return j.get_agents()


def get_agent_launcher(agent_config: etree.Element):
    launcher = agent_config.find("launcher")
    launcher_class = launcher.attrib['class']
    return launcher_class, launcher


manager = Manager()
agent_candidates = manager.list()
agent_info = manager.list()
agent_info_group_by = manager.dict()


def handle_agent(agent):
    ssh_client = SSHClient()
    ssh_client.set_missing_host_key_policy(AutoAddPolicy)
    name = agent['displayName']
    config = j.get_agent_config(name)
    launcher_class, launcher = get_agent_launcher(config)
    if launcher_class == SSH_LAUNCHER:
        host = launcher.find("host").text
    elif launcher_class == COMMAND_LAUNCHER:
        agent_command = launcher.find("agentCommand").text
        host = agent_command.split(" ")[-1]
    ssh_client.connect(host, port=22, username="gatekeeper.tvsw", password="sdetgatekeeper1!")
    # session = client.get_transport().open_session()
    _, stdout, _ = ssh_client.exec_command("nproc")
    no_of_threads = stdout.read().decode("utf8").strip()
    _, stdout2, _ = ssh_client.exec_command("free -h|grep Mem|awk  '{print $2}'g")
    mem_size = stdout2.read().decode("utf8").strip()
    labels = []
    for each_label in agent['assignedLabels']:
        labels.append(each_label['name'])
    label_string = ",".join(sorted(labels))
    agent_info.append(
        {"name": name, "host": host, "launcher_class": launcher_class, "no_of_threads": no_of_threads, "mem": mem_size,
         "labels": label_string})
    ssh_client.close()


if __name__ == "__main__":
    output_file = args.list_output
    writer = pd.ExcelWriter(output_file)
    agents = get_agents()
    agent_ci = list(filter(lambda agent: re.compile(f"swfarm-.*").match(agent['displayName']), agents))
    agent_no_ci = list(filter(lambda agent: not re.compile(f"swfarm-.*").match(agent['displayName']), agents))
    with Pool() as pool:
        r = pool.map(handle_agent, agent_ci)
        print(len(agent_info))
        b = []
        for each_agent in agent_info:
            if each_agent['host'] in agent_info_group_by:
                agent_info_group_by[each_agent['host']].append(each_agent)
            else:
                agent_info_group_by[each_agent['host']] = [each_agent]
            b.append([each_agent['name'], each_agent['host'], each_agent['launcher_class'], each_agent['no_of_threads'],
                      each_agent['mem'], each_agent['labels']])
        df = pd.DataFrame(b, columns=["name", "host", "launcher_class", "no_of_threads", "mem", "labels"])
        df.to_excel(excel_writer=writer)
        writer.close()
        for a in agent_info_group_by:
            print(a, agent_info_group_by[a])

import re

from jenkins_tools.common import Jenkins
import logging
from lxml import etree
import xml.etree.ElementTree as ElementTree

logger = logging.getLogger()
# User pytest - https://docs.pytest.org/en/latest/

def test_job_not_found():
    j = Jenkins('http://localhost:7070', 'admin', 'admin')
    try:
         r = j.get_job("test4")
    except Exception as err:
        assert type(err) == KeyError
    else:
        assert False

def test_job_found():
    j = Jenkins('http://localhost:7070', 'admin', 'admin')
    try:
         r = j.get_job("test3")
    except Exception as err:
        assert False
    else:
        assert True

def test_job_config_not_found():
    j = Jenkins('http://localhost:7070', 'admin', 'admin')
    try:
         r = j.get_job_config("test4")
    except Exception as err:
        logger.info("Error type: " + str(type(err)))
        assert type(err) == KeyError
    else:
        assert False

def test_job_config_found():
    j = Jenkins('http://localhost:7070', 'admin', 'admin')
    try:
         r = j.get_job_config("test3")
    except Exception as err:
        logger.info("Error type: " + str(type(err)))
        assert False
    else:
        assert True

def test_job_config_update():
    # Update job configuration and check it's ok or not
    from datetime import datetime
    j = Jenkins('http://localhost:7070', 'admin', 'admin')
    job_name = "test1"

    # Get a job's current configuration
    j_obj = j.get_job_config(job_name)
    job_config_root = ElementTree.fromstring(j_obj)
    shell_task_name = "hudson.tasks.Shell"
    # Find "Execute shell" task in 'builders' section
    shell_tasks = job_config_root.findall(f".//{shell_task_name}")
    i = 0
    # date_str: Key element to compare new configuration is equal to my expect
    date_str = str(datetime.now())
    # Change shell commands
    for each_task in shell_tasks:
        i = i + 1
        cmd_node = each_task.find("command")
        cmd_node.text = f"echo Build shell #{i}\necho {date_str}"
    conf_str = ElementTree.tostring(job_config_root).decode("utf8")
    # Update job configuration
    j.update_job_config("test1",data=conf_str)

    j2 = Jenkins('http://localhost:7070', 'admin', 'admin')
    # Get job configuration with other connection
    conf2_str = j2.get_job_config(job_name)
    new_conf_root = ElementTree.fromstring(conf2_str)
    # Check if same or not
    check_i = 0
    for each_task in new_conf_root.findall(f".//{shell_task_name}"):
        cmd_task = each_task.find("command")
        if re.compile(f".*{date_str}.*").search(cmd_task.text):
            check_i = check_i + 1
    assert check_i == 1

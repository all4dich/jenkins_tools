import json
import requests
import re
import os
jenkins_url = os.environ["J_URL"]
auth_info = (os.environ["J_USER"], os.environ["J_PASS"])
url = f"{jenkins_url}computer/api/json?pretty=true&tree=computer[displayName,numExecutor,idle,offline,assignedLabels[name],executors[idle]]"
r = requests.get(url, auth=auth_info)

# Get computer lists
target_labels = "wish"
computers = json.loads(r.text)["computer"]
all_labels = []
all_agents = []
busy_agents = []
non_busy_agents = []
for each_computer in computers:
    name = each_computer["displayName"]
    labels = list(map(lambda l: l["name"], each_computer["assignedLabels"]))
    all_labels = all_labels + labels
    if target_labels in labels:
        all_agents.append(each_computer)
        agent_non_available = len(list(filter(lambda e: e["idle"], each_computer['executors']))) == 0
        print(agent_non_available)
        if agent_non_available:
            busy_agents.append(each_computer)
        else:
            non_busy_agents.append(each_computer)
print(f"All: {len(all_agents)}")
print(all_agents)
print(f"Busy: {len(busy_agents)}")
print(busy_agents)
print(f"Idle: {len(non_busy_agents)}")
print(non_busy_agents)
filtered_labels = filter(lambda name: not re.compile("3090.*").match(name), all_labels)
print(set(filtered_labels))
print(r.status_code)

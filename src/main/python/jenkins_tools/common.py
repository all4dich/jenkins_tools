import json
import logging
import requests
from jenkins_tools.types import job_classes, agent_classes
from lxml import etree

#logging = logging.getLogger()
# logging.setLevel(logging.INFO)

#formatter = logging.Formatter('%(levelname)7s:%(filename)s:%(lineno)d:%(funcName)10s: %(message)s')

#ch = logging.StreamHandler()
# ch.setLevel(logging.INFO)
#ch.setFormatter(formatter)

#logging.addHandler(ch)

_build_fields = "number,url,result,timestamp"
_job_tree = f"&tree=jobs[_class,name,url,displayName,fullDisplayName,fullName,buildable,firstBuild[{_build_fields}]," \
            f"lastBuild[{_build_fields}]]"


class Jenkins:
    def __init__(self, url, username, password):
        if url[-1] == "/":
            url = url[:-1]
        self._url = url
        self._username = username
        self._password = password
        self._auth = (self._username, self._password)
        self._jobs = []
        self._flatted_jobs = []
        self._slaves = []
        self._master = []
        self._jobDict = {}
        self.get_jobs()

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def jobs(self):
        return self._jobs

    def _set_header(self, headers={}):
        # Get Crumb data
        crumb_url = f"{self._url}/crumbIssuer/api/json"
        logging.info(f"Getting crumb information from {crumb_url}")
        crumb_res = requests.get(url=crumb_url, auth=self._auth)
        if crumb_res.status_code == 200:
            crumb_json = json.loads(crumb_res.text)
            headers[crumb_json['crumbRequestField']] = crumb_json['crumb']
        return headers

    def get_jobs(self):
        """
        Get a list of all jobs including items under 'Folder' object
        :return: All jobs
        """
        self.check_connection()
        self._flatted_jobs = []
        while self._jobs:
            each_job = self._jobs.pop()
            self._flatted_jobs.append(each_job)
            self._jobDict[each_job['fullName']] = each_job
            if each_job['_class'] == job_classes.folder:
                r = self.get_object(each_job['url'], tree=_job_tree)
                jobs = r['jobs']
                each_job['jobs'] = jobs
                for sub_job in jobs:
                    if sub_job['_class'] == job_classes.folder:
                        self._jobs.append(sub_job)
                    else:
                        self._flatted_jobs.append(sub_job)
                        self._jobDict[sub_job['fullName']] = sub_job
        self._jobs = self._flatted_jobs
        return self._flatted_jobs

    def check_connection(self, tree=_job_tree):
        """
        Check if you can call Jenkins api with host and authentication information you provide
        :param tree: Set the range of returned data from Jenkins like "&tree=jobs[name]"
        :return: True if a connection is OK or False for other cases
        """
        jenkins_api_url = f"{self._url}/api/json?pretty=true{tree}"
        logging.info(f"Call {jenkins_api_url}")
        res = requests.get(jenkins_api_url, auth=self._auth)
        logging.info(f"Response code = {res.status_code}")
        if res.status_code == 200:
            res_json = json.loads(res.text)
            self._jobs = res_json['jobs']
            logging.info(f"You can connect to a Jenkins {self._url} with current authentication information")
            return True
        else:
            return False

    def get_object(self, url="", tree="", api_suffix="api/json?"):
        """
        Get Jenkins object(job, view, folder, agent.. )'s information from the web UI url

        :param url: Object's web UI url
        :return: Json Object
        """
        if api_suffix == "":
            tree = ""
        api_url = f"{url}{api_suffix}{tree}"
        logging.debug(f"API url to be called: {api_url}")
        res = requests.get(api_url, auth=self._auth)
        if res.status_code != 200:
            raise Exception(f"Call url = {api_url}, Error code = {res.status_code}. Check your request")
        else:
            try:
                res_json = json.loads(res.text)
            except:
                # Return an object's config.xml data
                return res.text
            else:
                # Return an object's detailed information
                return res_json

    def get_agent_config(self, agent_name):
        agent_url = f"{self._url}/computer/{agent_name}/"
        agent_config_url = f"{agent_url}config.xml"
        get_config_res = requests.get(agent_config_url, auth=self._auth)
        if get_config_res.status_code == 200:
            agent_config = etree.fromstring(get_config_res.text.encode("utf8"))
            return agent_config
        else:
            return None

    def get_agents(self):
        """
        Get a list of all agents and make a list of slaves and master
        All slaves are assigned to a variable 'self._slaves' and a master is assigned to 'self._master'

        :return: A list of slaves that its '_class' is 'hudson.slaves.SlaveComputer'
        """
        api_url = f"{self._url}/computer/"
        res = self.get_object(api_url,
                              tree="&tree=computer[_class,displayName,description,assignedLabels[name],idle,offline,absoluteRemotePath]")
        slaves = filter(lambda agent: agent['_class'] == agent_classes.slavecomputer, res['computer'])
        self._master = filter(lambda agent: agent['_class'] != agent_classes.slavecomputer, res['computer'])
        for each_slave in slaves:
            each_slave['labels'] = list(
                set(map(lambda each_label: each_label['name'], each_slave['assignedLabels']))
            )
            self._slaves.append(each_slave)
        return self._slaves

    def get_job(self, job_name):
        """
        Get a job uri and return its information

        :param job_name:
        :return:
        """
        returned_job = ""
        if len(self._flatted_jobs) == 0:
            self.get_jobs()
        return self._jobDict[job_name]

    def get_job_config(self, job_name):
        """
        Get job's name and return that job's config.xml data

        :param job_name:
        :return:
        """
        job_obj = self.get_job(job_name)
        job_url = job_obj['url']
        job_config_url = f"{job_url}config.xml"
        return self.get_object(url=job_config_url, tree="", api_suffix="")

    def get_job_builds(self, job_name):
        """
        Get a job's all builds

        :param job_name:
        :return:
        """
        job_obj = self.get_job(job_name)
        job_url = job_obj['url']
        builds_tree = "tree=builds[building,displayName,description,duration,fullDisplayName,id,number,queueId,result,url]"
        return self.get_object(job_url, tree=builds_tree)['builds']

    def delete_build(self, job_name, build_number):
        """
        Delete a build at job_name

        :param job_name:
        :param build_number:
        :return:
        """
        job_obj = self.get_job(job_name)
        job_url = job_obj['url']
        delete_build_url = f"{job_url}/{build_number}/doDelete"
        logging.info(f"Delete {job_name} #{build_number} build on {self.url}")
        logging.debug(f"Delete url: {delete_build_url}")
        build_del_req = requests.post(delete_build_url, auth=self._auth)
        if build_del_req.status_code != 200:
            logging.error(build_del_req.text)
            raise Exception(f"Deleting {job_name} #{build_number} has been failed")
        else:
            logging.warnin(f"Deleting {job_name} #{build_number} is done")

    def update_job_config(self, job_name, data=None):
        """
        Update a job's config.xml as new configuration data.

        :param job_name:
        :param data:
        :return:
        """
        job_info = self.get_job(job_name)
        job_config_url = f"{job_info['url']}config.xml"
        headers = self._set_header({"content-type": "application/xml"})
        job_update_req = requests.post(job_config_url, data=data, auth=self._auth, headers=headers)
        if job_update_req.status_code != 200:
            logging.error(job_update_req.text)
            raise Exception(f"Updating {job_name}'s config.xml has been failed")
        else:
            logging.info(f"Updating {job_name}'s config.xml is done with SUCCESS")

    def create_job(self, job_name, data):
        if job_name in self._jobDict:
            message = f"You have been trying to create a job '{job_name}' but it exists!"
            logging.warning(message)
            raise Exception(message)
        else:
            create_url = f"{self._url}/createItem?name={job_name}"
            job_url = f"{self._url}/job/{job_name}"
            headers = self._set_header({"content-type": "application/xml"})
            logging.info(f"Create a job {job_name} with the url {create_url}")
            create_job = requests.post(create_url, auth=self._auth, data=data, headers=headers)
            if create_job.status_code == 200:
                logging.info(f"Create a job {job_name}: SUCCESS")
                logging.info(f"Job url: {job_url}")
            else:
                logging.error(f"Create a job {job_name}: FAILED")
                logging.error(f"{create_job.text}")
                raise Exception(f"Create a job {job_name}: FAILED")

    def create_agent(self, agent_name, agent_type, data):
        # create_url = f"{self._url}/computer/doCreateItem?name={agent_name}&type={agent_type}"
        create_url = f"{self._url}/computer/doCreateItem"
        agent_url = f"{self._url}/computer/{agent_name}"
        headers = self._set_header({'Content-Type': 'application/x-www-form-urlencoded'})
        logging.info(f"Create an agent {agent_name} with the url {create_url}")
        # create_job = requests.post(create_url, auth=self._auth, data=data, headers=headers)
        if agent_name is not None and agent_type is not None:
            data['name'] = agent_name
            data['type'] = agent_type
        create_job = requests.post(create_url, auth=self._auth, data=data, headers=headers)
        if create_job.status_code == 200:
            logging.info(f"Create a agent {agent_name}: SUCCESS")
            logging.info(f"Job url: {agent_url}")
        else:
            logging.error(f"Create a agent {agent_name}: FAILED")
            logging.error(f"{create_job.text}")
            logging.error(f"{create_job.status_code}")
            raise Exception(f"Create a agent {agent_name}: FAILED")

    def delete_job(self, job_name):
        if job_name in self._jobDict:
            job_url = f"{self._url}/job/{job_name}"
            delete_url = f"{job_url}/doDelete"
            delete_request = requests.post(delete_url, auth=self._auth)
            if delete_request.status_code != 200:
                logging.error(f"INFO: Delete a job {job_name}")
            else:
                logging.error(f"{delete_request.status_code}")
                logging.error(f"When deleting {job_name}")
        else:
            logging.error(f"{job_name} doesn't exist on Jenkins. So you can't delete it.")

    def set_agent_offline(self, agent_name, description):
        agent_url = self.url + "/computer/" + agent_name + "/"
        res = self.get_object(agent_url, tree="&tree=offline")
        if res["offline"]:
            logging.error(f"Agent {agent_url} has been already offline mode")
            return True
        else:
            res_offline = requests.post(agent_url + "/toggleOffline", auth=self._auth,
                                        data={"offlineMessage": description})
            if res_offline.status_code != 200:
                logging.error(f"Can't set {agent_name} as offline mode. Please check {agent_url}")
                return False
            else:
                logging.warning(f"Done: {agent_name} has been set as offline")
                return True

    def get_build_parameters(self, job_name, number):
        logging.debug(f"Getting parameters from {job_name} #{number}")
        # params
        #   - Key: Parameter name
        #   - Value: Parameter value
        params = {}
        job_obj = self.get_job(job_name)
        build_url = job_obj['url'] + f"{number}/"
        build_parameter_tree = "&tree=actions[parameters[name,value]]"
        logging.debug(f"Build url: {build_url}, Build parameter tree: {build_parameter_tree}")
        build_param_data = self.get_object(build_url, tree=build_parameter_tree)
        param_class_val = "hudson.model.ParametersAction"
        param_actions = list(
            filter(lambda each_action: "_class" in each_action and each_action["_class"] == param_class_val,
                   build_param_data["actions"]))
        for param_action in param_actions:
            action_params = param_action["parameters"]
            for each_param in action_params:
                params[each_param['name']] = each_param['value']
        logging.debug(f"Number of parameters: {len(params)}")
        params['url'] = build_url
        return params

    def get_build_causes(self, job_name, number):
        logging.debug(f"Getting parameters from {job_name} #{number}")
        # params
        #   - Key: Parameter name
        #   - Value: Parameter value
        causes = []
        job_obj = self.get_job(job_name)
        build_url = job_obj['url'] + f"{number}/"
        build_cause_tree = "&tree=actions[causes[*]]"
        logging.debug(f"Build url: {build_url}, Build parameter tree: {build_cause_tree}")
        build_cause_data = self.get_object(build_url, tree=build_cause_tree)
        cause_class_val = "hudson.model.CauseAction"
        cause_actions = list(
            filter(lambda each_action: "_class" in each_action and each_action["_class"] == cause_class_val,
                   build_cause_data["actions"]))
        for cause_action in cause_actions:
            actions = cause_action["causes"]
            for each_cause in actions:
                causes.append(each_cause)
        logging.debug(causes)
        return causes

    def get_running_builds(self):
        logging.debug(f"Get a list of running builds on Jenkins {self.url}")
        computer_fields = "displayName,idle,offline,numExecutors"
        executor_fields = "idle,number,currentExecutable[fullDisplayName,number,url]"
        tree_data = f"tree=computer[{computer_fields},executors[{executor_fields}]]"
        get_url = self.url + "/computer/"
        res = self.get_object(get_url, tree=tree_data)
        agents = res["computer"]
        running_builds = []
        idle_executors = []
        idle_hosts = []
        busy_hosts = []
        for each_agent in agents:
            agent_name = each_agent["displayName"]
            executors = each_agent["executors"]
            for each_executor in executors:
                idle = each_executor['idle']
                if not idle:
                    running_builds.append({
                        "agent": agent_name,
                        "executor_number": each_executor['number'],
                        "build_number": each_executor['currentExecutable']['number'],
                        "build_name": each_executor['currentExecutable']['fullDisplayName'],
                        "build_url": each_executor['currentExecutable']['url']
                    })
                    busy_hosts.append(agent_name)
                else:
                    idle_executors.append([agent_name, each_executor])
                    idle_hosts.append(agent_name)
        return {"running_builds": running_builds, "busy_hosts": busy_hosts, "idle_hosts": idle_hosts}

    def get_git_build_data(self, job_name, build_number):
        logging.debug(f"Get git build data from {job_name} #{build_number}")
        job_obj = self.get_job(job_name)
        build_url = job_obj['url'] + f"{build_number}/"
        git_build_data_tree = "&tree=actions[_class,causes[userName],remoteUrls,buildsByBranchName[*[*]]]"
        logging.debug(f"Build url: {build_url}, Build parameter tree: {git_build_data_tree}")
        git_build_data = self.get_object(build_url, tree=git_build_data_tree)
        target_class_name = "hudson.plugins.git.util.BuildData"
        cause_class_name = "hudson.model.CauseAction"
        git_build_data_ele = list(
            filter(lambda each_action: "_class" in each_action and each_action["_class"] == target_class_name,
                   git_build_data["actions"]))
        build_causes_ele = list(
            filter(lambda each_action: "_class" in each_action and each_action["_class"] == cause_class_name,
                   git_build_data["actions"]))
        branch_info = git_build_data_ele[0]['buildsByBranchName']
        build_cause = build_causes_ele[0]['causes'][0]
        build_user = ""
        if "userName" in build_cause:
            build_user = build_cause['userName']

        branch_name = ""
        branch_sha1 = ""
        for each_key in branch_info.keys():
            branch_name = each_key.replace("origin/", "")
            branch_sha1 = branch_info[each_key]['revision']['SHA1']
        return {"branch_name": branch_name, "branch_commit": branch_sha1, "raw_data": git_build_data_ele[0],
                "requestor": build_user}

    def get_in_queue_builds(self):
        logging.debug(f"Get a list of running builds on Jenkins {self.url}")
        #tree_data = f"tree=items[*[*]]"
        tree_data = f"tree=items[_class,actions[*],id,inQueueSince,task[*],url,why,timestamp]"
        get_url = self.url + "/queue/"
        res = self.get_object(get_url, tree=tree_data)
        queued_items = res["items"]
        return queued_items

    def check_slot_available(self, target_label):
        logging.info(f"Check if available slots exist for label {target_label} on {self._url}")
        get_executors_url = f"{self._url}/computer/api/json?pretty=true&tree=computer[displayName,numExecutor,idle,offline,assignedLabels[name],executors[idle]]"
        get_executors = requests.get(get_executors_url, auth=self._auth)
        agents = json.loads(get_executors.text)["computer"]
        assigned_agents = []
        available_agents = []
        for each_agent in agents:
            agent_name = each_agent["displayName"]
            assigned_labels = list(map(lambda l: l["name"], each_agent["assignedLabels"]))
            if target_label in assigned_labels:
                assigned_agents.append(each_agent)
                agent_non_available = len(list(filter(lambda e: e["idle"], each_agent["executors"]))) == 0
                if agent_non_available:
                    logging.info("")
                else:
                    available_agents.append(each_agent)
        return len(available_agents) != 0

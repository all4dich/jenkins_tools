import json
import requests
import logging

from jenkins_tools.types import job_classes, agent_classes

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)7s:%(filename)s:%(lineno)d:%(funcName)10s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

logger.addHandler(ch)

_job_tree = "&tree=jobs[_class,name,url,displayName,fullDisplayName,fullName]"
class Jenkins:
    def __init__(self, url, username, password):
        self._url = url
        self._username = username
        self._password = password
        self._auth = (self._username, self._password)
        self._jobs = []
        self._flatted_jobs = []
        self._slaves = []
        self._master = []
        self._jobDict = {}

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
        logger.info(f"Getting crumb information from {crumb_url}")
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

    def check_connection(self,tree=_job_tree):
        """
        Check if you can call Jenkins api with host and authentication information you provide
        :param tree: Set the range of returned data from Jenkins like "&tree=jobs[name]"
        :return: True if a connection is OK or False for other cases
        """
        jenkins_api_url = f"{self._url}/api/json?pretty=true{tree}"
        logger.info(f"Call {jenkins_api_url}")
        res = requests.get(jenkins_api_url, auth=self._auth)
        logger.info(f"Response code = {res.status_code}")
        if res.status_code == 200:
            res_json = json.loads(res.text)
            self._jobs = res_json['jobs']
            logger.info(f"You can connect to a Jenkins {self._url} with current authentication information")
            return True
        else:
            return False

    def get_object(self,url="",tree="", api_suffix="api/json?"):
        """
        Get Jenkins object(job, view, folder, agent.. )'s information from the web UI url

        :param url: Object's web UI url
        :return: Json Object
        """
        if api_suffix == "":
            tree = ""
        api_url = f"{url}{api_suffix}{tree}"
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

    def get_agents(self):
        """
        Get a list of all agents and make a list of slaves and master
        All slaves are assigned to a variable 'self._slaves' and a master is assigned to 'self._master'

        :return: A list of slaves that its '_class' is 'hudson.slaves.SlaveComputer'
        """
        api_url = f"{self._url}/computer/"
        res = self.get_object(api_url,tree="&tree=computer[_class,displayName,description,assignedLabels[name],idle,offline,absoluteRemotePath]")
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
        return self.get_object(url=job_config_url,tree="",api_suffix="")

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
        logger.info(f"Delete {job_name} #{build_number} build on {self.url}")
        logger.debug(f"Delete url: {delete_build_url}")
        build_del_req = requests.post(delete_build_url, auth=self._auth)
        if build_del_req.status_code != 200:
            logger.error(build_del_req.text)
            raise Exception(f"Deleting {job_name} #{build_number} has been failed")
        else:
            logger.info(f"Deleting {job_name} #{build_number} is done")

    def update_job_config(self,job_name,data=None):
        """
        Update a job's config.xml as new configuration data.

        :param job_name:
        :param data:
        :return:
        """
        job_info = self.get_job(job_name)
        job_config_url = f"{job_info['url']}config.xml"
        headers = self._set_header({ "content-type": "application/xml" })
        job_update_req = requests.post(job_config_url, data=data, auth=self._auth, headers=headers)
        if job_update_req.status_code != 200:
            logger.error(job_update_req.text)
            raise Exception(f"Updating {job_name}'s config.xml has been failed")
        else:
            logger.info(f"Updating {job_name}'s config.xml is done with SUCCESS")

    def create_job(self, job_name,data):
        if job_name in self._jobDict:
            message = f"You have been trying to create a job '{job_name}' but it exists!"
            logger.warning(message)
            raise Exception(message)
        else:
            create_url = f"{self._url}/createItem?name={job_name}"
            job_url = f"{self._url}/job/{job_name}"
            headers = self._set_header({"content-type": "application/xml"})
            logger.info(f"Create a job {job_name} with the url {create_url}")
            create_job = requests.post(create_url, auth=self._auth, data=data, headers=headers)
            if create_job.status_code == 200:
                logger.info(f"Create a job {job_name}: SUCCESS")
                logger.info(f"Job url: {job_url}")
            else:
                logger.error(f"Create a job {job_name}: FAILED")
                logger.error(f"{create_job.text}")
                raise Exception(f"Create a job {job_name}: FAILED")

    def set_agent_offline(self, agent_name):
        agent_url = self.url + "/computer/" + agent_name + "/"
        res = self.get_object(agent_url, tree="&tree=offline")
        if res["offline"]:
            logger.error(f"Agent {agent_url} has been already offline mode")
            return True
        else:
            res_offline = requests.post(agent_url+"/toggleOffline", auth=self._auth)
            if res_offline.status_code != 200:
                logger.error(f"Can't set {agent_name} as offline mode. Please check {agent_url}")
                return False
            else:
                logger.warning(f"Done: {agent_name} has been set as offline")
                return True

import json
import requests
import logging

from jenkins_tools.types import job_classes

logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(levelname)7s:%(filename)s:%(lineno)d:%(funcName)10s: %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)

logger.addHandler(ch)

class Jenkins:
    def __init__(self, url, username, password):
        self._url = url
        self._username = username
        self._password = password
        self._auth = (self._username, self._password)
        self._jobs = []
        self._flatted_jobs = []

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def jobs(self):
        return self._jobs

    def get_jobs(self):
        """
        Get a list of all jobs including items under 'Folder' object
        :return: All jobs
        """
        self.check_connection()
        self._flatted_jobs = []
        for each_job in self._jobs:
            self._flatted_jobs.append(each_job)
            if each_job['_class'] == job_classes.folder:
                r = self.get_object(each_job['url'])
                jobs = r['jobs']
                each_job['jobs'] = jobs
                self._flatted_jobs = list(self._flatted_jobs + jobs)
        return self._flatted_jobs

    def check_connection(self,tree=""):
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

    def get_object(self,url=""):
        """
        Get Jenkins object(job, view, folder, agent.. )'s information from the web UI url

        :param url: Object's web UI url
        :return: Json Object
        """
        api_url = f"{url}api/json"
        res = requests.get(api_url, auth=self._auth)
        if res.status_code != 200:
            raise Exception(f"Call url = {api_url}, Error code = {res.status_code}. Check your request")
        else:
            res_json = json.loads(res.text)
            return res_json

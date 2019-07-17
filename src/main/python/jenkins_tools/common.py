import json
import requests
import logging

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

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        self._url = value

    @property
    def jobs(self):
        return self._jobs

    def check_connection(self,tree=""):
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

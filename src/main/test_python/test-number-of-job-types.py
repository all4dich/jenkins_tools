import unittest
from jenkins_tools.common import Jenkins
from jenkins_tools.types import job_classes

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class TestNumberOfJobs(unittest.TestCase):
    def test_case1_allJobs(self):
        j = Jenkins('http://localhost:7070', 'admin', 'admin')
        j.get_jobs()
        self.assertEqual(10, len(j.jobs))

    def test_case1_folderJobs(self):
        j = Jenkins('http://localhost:7070', 'admin', 'admin')
        r = j.get_jobs()
        i = 0
        for each_job in r:
            if each_job['_class'] == job_classes.folder:
                i = i + 1
        self.assertEqual(4,i)

    def test_case1_freeStyleJobs(self):
        j = Jenkins('http://localhost:7070', 'admin', 'admin')
        r = j.get_jobs()
        i = 0
        for each_job in r:
            if each_job['_class'] == job_classes.free_style:
                i = i + 1
        self.assertEqual(5,i)

    def test_case1_workflowJobs(self):
        j = Jenkins('http://localhost:7070', 'admin', 'admin')
        r = j.get_jobs()
        i = 0
        for each_job in r:
            if each_job['_class'] == job_classes.workflow:
                i = i + 1
        self.assertEqual(1,i)


if __name__ == '__main__':
    unittest.main()

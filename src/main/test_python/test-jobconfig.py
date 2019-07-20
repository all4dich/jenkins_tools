import unittest
import json
from jenkins_tools.common import Jenkins

j = Jenkins("http://localhost:7070", "admin", "admin")
r = j.get_jobs()
r2 = j.get_job("folder1/test3")
print(json.dumps(r2, indent=4, sort_keys=True))
print(r2['fullDisplayName'])

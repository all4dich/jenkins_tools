from jenkins_tools.common import Jenkins

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

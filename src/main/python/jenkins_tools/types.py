class JobClasses:
    def __init__(self):
        self._folder = "com.cloudbees.hudson.plugins.folder.Folder"
        self._free_style = "hudson.model.FreeStyleProject",
        self._workflow = "org.jenkinsci.plugins.workflow.job.WorkflowJob"

    @property
    def folder(self):
        return self._folder

    @property
    def free_style(self):
        return self._free_style

    @property
    def workflow(self):
        return self._workflow

job_classes = JobClasses()


class AgentClasses:
    def __init__(self):
        self._slavecomputer= "hudson.slaves.SlaveComputer"

    @property
    def slavecomputer(self):
        return self._slavecomputer


agent_classes = AgentClasses()


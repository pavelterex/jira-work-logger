from jira import JIRA


class WorkAutoLogger:
    def __init__(self, settings):
        self.settings = settings

    def execute(self):
        print('logger executed')
        return

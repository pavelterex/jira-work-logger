from jira import JIRA


class MainWorker:
    def __init__(self, settings):
        self.settings = settings
        self._conn = None

    @property
    def conn(self):
        if not self._conn:
            self._conn = self.establish_connection()
        return self._conn

    def establish_connection(self):
        try:
            conn = JIRA(server=self.settings['jira_host'],
                        basic_auth=(self.settings['jira_user'], self.settings['jira_pass']))
        except Exception as exn:
            print(exn)
            return

        return conn

    def execute(self):
        issues = self.get_issues_by_status_within_period('DOING')
        return

    def get_issues_by_status_within_period(self, status: str):
        from_date = self.settings['from_date']
        to_date = self.settings['to_date']
        query = f'assignee = currentUser() AND Status was "{status}" DURING ("{from_date}","{to_date}")'
        issues = self.conn.search_issues(jql_str=query)
        return issues


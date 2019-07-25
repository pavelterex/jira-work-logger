from typing import Union, Iterable
from datetime import datetime, timedelta

from jira import JIRA
from .constants import *


class LogWorker:
    def __init__(self, settings):
        self.settings = settings
        self._conn = None
        self._loaded_issues = None
        self._loaded_worklogs = None
        self._work_dates = None

    @property
    def conn(self):
        if not self._conn:
            self._conn = self.establish_connection()

        return self._conn

    @property
    def loaded_issues(self):
        if not self._loaded_issues:
            self._loaded_issues = self.load_issues(ISSUE_ACTIVE_STATUSES, self.settings['work_days'])

        return self._loaded_issues

    @property
    def loaded_worklogs(self):
        if not self._loaded_worklogs:
            self._loaded_worklogs = {}

            for issue in self.loaded_issues:
                self._loaded_worklogs[issue.key] = issue.fields.worklog.worklogs

        return self._loaded_worklogs

    @property
    def work_dates(self):
        if not self._work_dates:
            self._work_dates = self.get_work_dates_for_period()
        return self._work_dates

    def establish_connection(self):
        try:
            conn = JIRA(server=self.settings['jira_host'],
                        basic_auth=(self.settings['jira_user'], self.settings['jira_pass']))
        except Exception as exn:
            print(exn)
            return
        return conn

    def load_issues(self, status: Union[str, Iterable]= '', date: Union[str, Iterable]= ''):
        """Load loaded_issues that can be filtered by statuses and\or dates"""
        status_filter = f' AND Status was "{status}"' if isinstance(status, str) else f' AND Status was IN ({status})'
        date_filter = f' ON "{date}"' if isinstance(date, str) else f' DURING ("{date[0]}","{date[1]}")'
        query = f'assignee = currentUser(){status_filter}{date_filter}'
        issues = self.conn.search_issues(jql_str=query, fields=ISSUE_FIELDS)
        return issues

    def calculate_logged_time_for_date(self, date: str):
        """Calculate already logged time in seconds for given date"""
        seconds_logged = 0
        flatten_worklogs = [item for sublist in self.loaded_worklogs.values() for item in sublist]

        for item in flatten_worklogs:
            if item.started.split('T')[0] == date:
                seconds_logged += item.timeSpentSeconds

        return seconds_logged

    def get_work_dates_for_period(self):
        """Get work dates from given dates range using given work weekdays filter"""
        start_date = datetime.strptime(self.settings['from_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(self.settings['to_date'], '%Y-%m-%d').date()
        work_wdays = [IsoWeekdays[day[0]] for day in list(self.settings['days_filter'].items()) if day[1]]

        work_dates = []
        for n in range(int((end_date - start_date).days) + 1):
            _date = start_date + timedelta(n)

            if _date.isoweekday() in work_wdays:
                work_dates.append(_date)

        return work_dates

    def execute_autologging(self):
        work_dates = self.get_work_dates_for_period()

        # Processing day by day
        for _date in work_dates:
            logged_hrs = self.calculate_logged_time_for_date(str(_date))
            needed_hrs = self.settings['target_hrs'] - logged_hrs

            if needed_hrs <= 0:
                print(f'Date {str(_date)} already has {logged_hrs} hours logged')
                continue






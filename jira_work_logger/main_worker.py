from typing import Union, Iterable
from datetime import datetime, timedelta

from jira import JIRA
from .constants import *


class MainWorker:
    def __init__(self, settings):
        self.settings = settings
        self._conn = None
        self._issues = None
        self._work_dates = None

    @property
    def conn(self):
        if not self._conn:
            self._conn = self.establish_connection()
        return self._conn

    @property
    def issues(self):
        if not self._issues:
            self._issues = self.get_issues(ISSUE_ACTIVE_STATUSES, self.settings['work_days'])
        return self._issues

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

    def get_issues(self, status: Union[str, Iterable]='', date: Union[str, Iterable]=''):
        """Get issues that can be filtered by statuses and\or dates"""
        status_filter = f' AND Status was "{status}"' if isinstance(status, str) else f' AND Status was IN ({status})'
        date_filter = f' ON "{date}"' if isinstance(date, str) else f' DURING ("{date[0]}","{date[1]}")'
        query = f'assignee = currentUser(){status_filter}{date_filter}'
        issues = self.conn.search_issues(jql_str=query, expand='worklog')
        return issues

    def get_logged_time(self, date: Union[str, Iterable]=''):
        """Get already logged time in seconds within given date or period"""
        sec_logged = 0

        for _issue in self.issues:


        return sec_logged


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

        # for _date in work_dates:

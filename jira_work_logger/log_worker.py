from datetime import datetime, timedelta
from typing import Union, Iterable

from PyQt5.QtCore import pyqtSignal
from jira import JIRA

from .constants import *


class LogWorker:
    # log_msg = pyqtSignal(str)

    def __init__(self, settings):
        self.settings = settings
        self._conn = None
        self._loaded_tasks = None
        self._loaded_worklogs = None
        self._work_dates = None

    @property
    def conn(self):
        if not self._conn:
            self._conn = self.establish_connection()

        return self._conn

    @property
    def loaded_tasks(self):
        if not self._loaded_tasks:
            task_statuses = (TASK_INPROGRESS_STATUS, TASK_REVIEW_STATUS)
            self._loaded_tasks = self.load_tasks(task_statuses, (self.settings['from_date'], self.settings['to_date']))

        return self._loaded_tasks

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

    def load_tasks(self, status: Union[str, Iterable] = '', date: Union[str, Iterable] = ''):
        """Load tasks that can be filtered by statuses and(or) dates"""
        status_filter = f' AND Status was "{status}"' if isinstance(status, str) else f' AND Status was IN {status}'
        date_filter = f' ON "{date}"' if isinstance(date, str) else f' DURING ("{date[0]}","{date[1]}")'
        query = f'assignee = currentUser(){status_filter}{date_filter}'
        tasks = self.conn.search_issues(jql_str=query, maxResults=1000)
        return tasks

    def calculate_logged_seconds_for_date(self, date: str):
        """Calculate already logged time in seconds by user for given date"""
        seconds_logged = 0
        query = f'worklogAuthor = currentUser() AND worklogDate = {date}'
        logged_tasks = self.conn.search_issues(query)
        user_worklogs = []

        for task in logged_tasks.iterable:
            task_wlogs = [wlog for wlog in self.conn.worklogs(task.key) if wlog.started.split('T')[0] == date and
                          wlog.author.name == self.settings['jira_user']]
            user_worklogs.extend(task_wlogs)

        for item in user_worklogs:
            seconds_logged += item.timeSpentSeconds

        return seconds_logged

    def get_work_dates_for_period(self):
        """Get work dates from given dates range using given work weekdays filter"""
        start_date = datetime.strptime(self.settings['from_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(self.settings['to_date'], '%Y-%m-%d').date()
        work_wdays = [IsoWeekdays[day[0]] for day in list(self.settings['work_days'].items()) if day[1]]

        work_dates = []
        for n in range(int((end_date - start_date).days) + 1):
            _date = start_date + timedelta(n)

            if _date.isoweekday() in work_wdays:
                work_dates.append(str(_date))

        return work_dates

    def execute_autologging(self):
        # Defining whole list of work dates to be iterated through
        self.log_msg.emit('Process started')
        work_dates = self.get_work_dates_for_period()

        # Processing date by date
        for _date in work_dates:
            # TODO: Get rid of time hard code
            date = datetime.strptime(f'{_date}T06:00:40-0500', '%Y-%m-%dT%H:%M:%S%z')
            logged_sec = self.calculate_logged_seconds_for_date(str(_date))
            needed_sec = (self.settings['target_hrs'] * 3600) - logged_sec

            if needed_sec <= 0:
                print(f'{str(_date)}: {round(logged_sec / 3600, 2)} hours already logged')
                continue

            # Building a list with all available tasks for this date that can produce work log
            # Tasks will have a priority among themselves, so ones with the highest priority will be used first for
            # logging work.
            # High priority - tasks that were specified implicitly via GUI like "daily" ones
            # Medium priority - tasks with status like "in progress"
            # Low priority - tasks with status like "verifying"

            ranked_tasks = {
                'high': list(self.settings['daily_tasks'].items()),
                'medium': self.load_tasks(TASK_INPROGRESS_STATUS, _date).iterable,
                'low': self.load_tasks(TASK_REVIEW_STATUS, _date).iterable
            }

            # Removing occurrencies of Med tasks in Low tasks if any
            ranked_tasks['low'] = [task for task in ranked_tasks['low'] if task not in ranked_tasks['medium']]

            # Beginning of work logging cycle within High priority tasks
            # In this case we log work for every task if amount of time to be logged won't exceed needed time amount
            while ranked_tasks['high'] and needed_sec:
                task, time_str = ranked_tasks['high'].pop()
                time_sec = str_to_sec(time_str)
                if needed_sec - time_sec < 0:
                    self.conn.add_worklog(task, timeSpentSeconds=time_sec - needed_sec, started=date)
                    needed_sec = 0
                else:
                    self.conn.add_worklog(task, timeSpentSeconds=time_sec, started=date)
                    needed_sec -= time_sec

            # Beginning of work logging cycle within Medium and Low Priority task
            if len(ranked_tasks['medium']) and ranked_tasks['low']:
                time_per_med = ((needed_sec / 3600) // len(ranked_tasks['medium'])) * 3600
                time_per_low = ((needed_sec / 3600) % len(ranked_tasks['medium'])) * 3600

                for task in ranked_tasks['medium']:
                    self.conn.add_worklog(task.key, timeSpentSeconds=time_per_med, started=date)

                if time_per_low:
                    self.conn.add_worklog(ranked_tasks['low'][0], timeSpentSeconds=time_per_low, started=date)

            elif len(ranked_tasks['medium']) and not ranked_tasks['low']:
                time_per_med = ((needed_sec / 3600) / len(ranked_tasks['medium'])) * 3600

                for task in ranked_tasks['medium']:
                    self.conn.add_worklog(task.key, timeSpentSeconds=time_per_med, started=date)

            elif not len(ranked_tasks['medium']) and ranked_tasks['low']:
                time_per_low = ((needed_sec / 3600) % len(ranked_tasks['medium'])) * 3600

                for task in ranked_tasks['low']:
                    self.conn.add_worklog(task.key, timeSpentSeconds=time_per_low, started=date)

            elif not len(ranked_tasks['medium']) and not ranked_tasks['low']:
                print(f'{_date}: No medium or low priority tasks provided!')

            # Summarizing results
            currently_logged_sec = self.calculate_logged_seconds_for_date(str(_date))
            diff_sec = (self.settings['target_hrs'] * 3600) - currently_logged_sec

            if not diff_sec:
                print(f'{_date}: Worklog is fully completed with {self.settings["target_hrs"]} hours as required.')
            elif diff_sec > 0:
                print(f'{_date}: Worklog still require {diff_sec / 3600} hours to be logged!')
            elif diff_sec < 0:
                print(f'{_date}: Worklog has been overlogged by {abs(diff_sec) / 3600} hours!')

        return



def str_to_sec(time_str: str):
    if time_str[-1] in 'dhms':
        return int(time_str[:-1]) * TimeToSec[time_str[-1]]

from datetime import datetime, timedelta
from typing import Union, Iterable

from PyQt5.QtCore import pyqtSignal, QObject
from jira import JIRA, JIRAError

from .constants import *


class LogWorker(QObject):
    msg = pyqtSignal(str)
    warn = pyqtSignal(str)
    err = pyqtSignal(str)

    def __init__(self, params):
        super().__init__()
        self.settings = params
        self.conn = None
        self._loaded_tasks = None
        self._loaded_worklogs = None
        self._work_dates = None

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
            self.msg.emit('Establishing connection to JIRA server...')
            conn = JIRA(server=self.settings['jira_host'], validate=True, max_retries=0,
                        basic_auth=(self.settings['jira_user'], self.settings['jira_pass']))
            self.msg.emit('Connection established successfully')
            return conn
        except JIRAError as exn:
            self.err.emit(f'Connection to JIRA server could not be established! JiraError HTTP {exn.status_code}')
            return None
        except Exception as exn:
            self.err.emit(f'Connection to JIRA server could not be established! {str(exn)}')
            return None

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

    def execute_logging(self):
        self.msg.emit(f'Auto logging worker started for dates range from {self.settings["from_date"]} to '
                      f'{self.settings["to_date"]}')

        # Establish connection to JIRA server
        self.conn = self.establish_connection()

        if not self.conn:
            self.thread().quit()
            return

        # Defining whole list of work dates to be iterated through
        work_dates = self.get_work_dates_for_period()
        self.msg.emit(f'{len(work_dates)} working day(s) found')

        # Processing date by date
        for _date in work_dates:
            self.msg.emit(f'Starting to process date {_date}')
            # TODO: Get rid of time hard code
            date = datetime.strptime(f'{_date}T06:00:40-0500', '%Y-%m-%dT%H:%M:%S%z')
            logged_sec = self.calculate_logged_seconds_for_date(str(_date))
            needed_sec = (self.settings['target_hrs'] * 3600) - logged_sec
            self.msg.emit(f'{logged_sec / 3600} hour(s) currently logged')

            if needed_sec <= 0:
                self.msg.emit('No additional time need to be logged')
                continue
            else:
                self.msg.emit(f'{needed_sec / 3600} hour(s) need to be logged')

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

            # Removing occurrences of Med tasks in Low tasks if any
            ranked_tasks['low'] = [task for task in ranked_tasks['low'] if task not in ranked_tasks['medium']]
            overall_tasks_found = len(ranked_tasks['high']) + len(ranked_tasks['medium']) + len(ranked_tasks['low'])
            self.msg.emit(f'Totally {overall_tasks_found} suitable task(s) found for this date')

            # Beginning of work logging cycle within High priority tasks
            # In this case we log work for every task if amount of time to be logged won't exceed needed time amount
            while ranked_tasks['high'] and needed_sec:
                task, time_str = ranked_tasks['high'].pop()
                time_sec = str_to_sec(time_str)
                if needed_sec - time_sec < 0:
                    self.conn.add_worklog(task, timeSpentSeconds=time_sec - needed_sec, started=date)
                    self.msg.emit(f'Work logged for task {task} = {time_sec / 3600} hour(s)')
                    needed_sec = 0
                else:
                    self.conn.add_worklog(task, timeSpentSeconds=time_sec, started=date)
                    self.msg.emit(f'Work logged for task {task} = {time_sec / 3600} hour(s)')
                    needed_sec -= time_sec

            # Beginning of work logging cycle within Medium and Low Priority task
            if len(ranked_tasks['medium']) and ranked_tasks['low']:
                time_per_med = ((needed_sec / 3600) // len(ranked_tasks['medium'])) * 3600
                time_per_low = ((needed_sec / 3600) % len(ranked_tasks['medium'])) * 3600

                for task in ranked_tasks['medium']:
                    self.conn.add_worklog(task.key, timeSpentSeconds=time_per_med, started=date)
                    self.msg.emit(f'Work logged for task {task.key} = {time_per_med / 3600} hour(s)')

                if time_per_low:
                    task = ranked_tasks['low'][0]
                    self.conn.add_worklog(task.key, timeSpentSeconds=time_per_low, started=date)
                    self.msg.emit(f'Work logged for task {task.key} = {time_per_low / 3600} hour(s)')

            elif len(ranked_tasks['medium']) and not ranked_tasks['low']:
                time_per_med = ((needed_sec / 3600) / len(ranked_tasks['medium'])) * 3600

                for task in ranked_tasks['medium']:
                    self.conn.add_worklog(task.key, timeSpentSeconds=time_per_med, started=date)
                    self.msg.emit(f'Work logged for task {task.key} = {time_per_med / 3600} hour(s)')

            elif not len(ranked_tasks['medium']) and ranked_tasks['low']:
                time_per_low = ((needed_sec / 3600) % len(ranked_tasks['medium'])) * 3600

                for task in ranked_tasks['low']:
                    self.conn.add_worklog(task.key, timeSpentSeconds=time_per_low, started=date)
                    self.msg.emit(f'Work logged for task {task.key} = {time_per_low / 3600} hour(s)')

            elif not len(ranked_tasks['medium']) and not ranked_tasks['low']:
                self.warn.emit(f'Not enough tasks for sufficient time logging in {_date}!')

            # Summarizing results
            summary_msg = f'Summary for {_date}: Work log'
            currently_logged_sec = self.calculate_logged_seconds_for_date(str(_date))
            diff_sec = (self.settings['target_hrs'] * 3600) - currently_logged_sec

            if not diff_sec:
                self.msg.emit(f'{summary_msg} fully completed with {self.settings["target_hrs"]} hour(s)')
            elif diff_sec > 0:
                self.warn.emit(f'{summary_msg} still require {diff_sec / 3600} hour(s) to be logged!')
            elif diff_sec < 0:
                self.warn.emit(f'{summary_msg} overloaded by {abs(diff_sec) / 3600} hour(s)!')

        self.msg.emit(f'Auto logging worker successfully finished')
        self.thread().quit()


def str_to_sec(time_str: str):
    if time_str[-1] in 'hms':
        return int(time_str[:-1]) * TimeToSec[time_str[-1]]

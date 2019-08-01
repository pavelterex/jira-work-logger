from enum import IntEnum

APP_VERSION = '1.0'
WEEKDAYS = {
    'MO': True,
    'TU': True,
    'WE': True,
    'TH': True,
    'FR': True,
    'SA': False,
    'SU': False
}
PARAMS = {
    'jira_host': '',
    'jira_user': '',
    'jira_pass': '',
    'work_days': {},
    'target_hrs': '',
    'daily_only': False,
    'daily_tasks': {},
    'tasks_comment': '',
    'from_date': '',
    'to_date': ''
}
MANDATORY_PARAMS = ['jira_host', 'jira_user', 'jira_pass', 'from_date', 'to_date']

TASK_INPROGRESS_STATUS = 'DOING'
TASK_REVIEW_STATUS = 'VERIFYING'
CONFIG_FILE = 'config.yaml'


class IsoWeekdays(IntEnum):
    MO = 1
    TU = 2
    WE = 3
    TH = 4
    FR = 5
    SA = 6
    SU = 7


class TimeToSec(IntEnum):
    h = 3600
    m = 60
    s = 1

from enum import IntEnum

APP_VERSION = '0.1'
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
    'extra_tasks': {},
    'from_date': '',
    'to_date': ''
}
MANDATORY_PARAMS = ['jira_host', 'jira_user', 'jira_pass', 'from_date', 'to_date']
ISSUE_ACTIVE_STATUSES = ['DOING', 'VERIFYING']
ISSUE_FIELDS = ['assignee', 'components', 'created', 'creator', 'description', 'issuetype', 'labels', 'priority',
                'project', 'reporter', 'resolution', 'resolutiondate', 'status', 'subtasks', 'summary', 'timespent',
                'updated', 'worklog']


class IsoWeekdays(IntEnum):
    MO = 1
    TU = 2
    WE = 3
    TH = 4
    FR = 5
    SA = 6
    SU = 7

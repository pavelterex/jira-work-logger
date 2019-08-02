from datetime import datetime
from pathlib import Path

import yaml
from PyQt5.QtCore import Qt, QThread, QRegExp, QDate
from PyQt5.QtGui import QIcon, QColor, QRegExpValidator
from PyQt5.QtWidgets import (QMainWindow, QAction, qApp, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QDoubleSpinBox,
                             QPushButton, QFormLayout, QLineEdit, QLabel, QCalendarWidget, QCheckBox, QGridLayout,
                             QTextEdit, QTabWidget, QFrame)

from jira_work_logger.constants import *
from jira_work_logger.log_worker import LogWorker


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setObjectName('main_window')
        self.params = PARAMS
        self.load_config()
        self.menubar = self.menuBar()
        self.root = QTabWidget(self)
        self.configurator = LoggerConfigurator(self.root)
        self.console = LoggerConsole(self.root)
        self.worker = None
        self.worker_thread = None
        self.init_ui()
        self.update_start_button()

    def init_ui(self):
        # Setting window geometry
        self.setWindowTitle('JIRA work logger')
        self.setWindowIcon(QIcon('gui/misc/clock-icon.ico'))

        # Setting menu bar
        app_menu = self.menubar.addMenu('Help')
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(qApp.quit)
        app_menu.addAction(exit_action)

        # Setting root frame
        self.root.addTab(self.configurator, 'Logger Setup')
        self.root.addTab(self.console, 'Logger Output')
        self.setCentralWidget(self.root)

    def setup_worker_thread(self):
        self.worker = LogWorker(self.params)
        self.worker_thread = QThread()
        self.worker.moveToThread(self.worker_thread)

        # Assign signals to slots
        self.worker.msg.connect(self.console.print_msg)
        self.worker.warn.connect(self.console.print_warn)
        self.worker.err.connect(self.console.print_err)
        self.worker_thread.started.connect(self.worker.execute_logging)
        self.worker_thread.finished.connect(self.stop_worker_thread)

    def execute_autologging(self):
        get_main_window().findChild(QWidget, 'main_buttons', Qt.FindChildrenRecursively).start_btn.setDisabled(True)
        self.read_params()
        self.setup_worker_thread()
        self.root.setCurrentIndex(1)
        qApp.processEvents()
        self.worker_thread.start()

    def stop_worker_thread(self):
        self.console.print_msg('Worker thread has been stopped')
        self.worker_thread.deleteLater()
        get_main_window().findChild(QWidget, 'main_buttons', Qt.FindChildrenRecursively).start_btn.setEnabled(True)
        qApp.processEvents()

    def update_start_button(self):
        self.read_params()
        start_btn = self.findChild(QWidget, 'main_buttons', Qt.FindChildrenRecursively).start_btn

        if not [param for param in MANDATORY_PARAMS if not self.params[param]]:
            if True in list(self.params['tasks_filter'].values()):
                start_btn.setEnabled(True)
                return

        start_btn.setDisabled(True)

    def read_params(self):
        """Reading params from widgets across Configurator"""
        # JIRA settings
        jira_widget = self.findChild(QWidget, 'jira_settings', Qt.FindChildrenRecursively)
        self.params['jira_host'] = jira_widget.host_ln.text()
        self.params['jira_user'] = jira_widget.user_ln.text()
        self.params['jira_pass'] = jira_widget.pass_ln.text()

        # Tasks filter settings
        tasks_filter_widget = self.findChild(QWidget, 'tasks_filter', Qt.FindChildrenRecursively)
        self.params['tasks_filter']['user_assignee'] = tasks_filter_widget.is_assignee.isChecked()
        self.params['tasks_filter']['user_validator'] = tasks_filter_widget.is_validator.isChecked()
        self.params['tasks_filter']['user_creator'] = tasks_filter_widget.is_creator.isChecked()

        # Working days settings
        days_widget = self.findChild(QWidget, 'days_config', Qt.FindChildrenRecursively)
        self.params['work_days'] = days_widget.weekdays
        self.params['target_hrs'] = days_widget.target_hrs.value()
        self.params['daily_tasks'] = tasks_string_to_dict(days_widget.daily_tasks.text())
        self.params['tasks_comment'] = days_widget.tasks_comment.text()
        self.params['daily_only'] = days_widget.daily_only.isChecked()
        self.params['ignore_tasks'] = tasks_string_to_list(days_widget.ignore_tasks.text())

        # Date settings
        date_widget = self.findChild(QWidget, 'dates_selector', Qt.FindChildrenRecursively)
        self.params['from_date'] = date_widget.from_cal.selectedDate().toString(Qt.ISODate)
        self.params['to_date'] = date_widget.to_cal.selectedDate().toString(Qt.ISODate)

    def load_config(self):
        config_path = Path(CONFIG_FILE)

        if config_path.exists():
            self.params.update(yaml.load(config_path.read_text(), Loader=yaml.FullLoader))
            return


class LoggerConfigurator(QWidget):
    def __init__(self, parent):
        super().__init__(parent, Qt.Widget)
        self.setObjectName('logger_configurator')
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(UpperSettingsPanel(self), 0, Qt.AlignTop)
        self.layout.addWidget(DateSelector(self), 0, Qt.AlignTop)
        self.layout.addWidget(MainButtons(self), 0, Qt.AlignRight)


class LoggerConsole(QWidget):
    def __init__(self, parent):
        super().__init__(parent, Qt.Widget)
        self.setObjectName('logger_console')
        self.layout = QGridLayout(self)

        self.output = QTextEdit(self)
        self.output.setReadOnly(True)
        self.layout.addWidget(self.output, 0, 0)

    def print_msg(self, msg: str):
        self.output.setTextColor(QColor(0, 0, 0))
        timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
        message = f'{timestamp} [L]  {msg}'
        self.output.append(message)

    def print_warn(self, warn: str):
        self.output.setTextColor(QColor(255, 140, 0))
        timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
        message = f'{timestamp} [W]  {warn}'
        self.output.append(message)

    def print_err(self, err: str):
        self.output.setTextColor(QColor(178, 34, 34))
        timestamp = datetime.now().strftime('[%Y-%m-%d %H:%M:%S]')
        message = f'{timestamp} [E]  {err}'
        self.output.append(message)


class UpperSettingsPanel(QWidget):
    def __init__(self, parent):
        super().__init__(parent, Qt.Widget)
        self.parent = parent
        self.setObjectName('upper_settings')

        layout = QGridLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(JiraSettings(self), 0, 0, 1, 1)
        layout.addWidget(DaysConfigurator(self), 0, 1, 2, 1)
        layout.addWidget(TasksFilterSettings(self), 1, 0, 1, 1)


class JiraSettings(QGroupBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName('jira_settings')
        self.setTitle('JIRA connection settings')
        self.setAlignment(Qt.AlignHCenter)

        layout = QFormLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setLabelAlignment(Qt.AlignRight)

        self.host_ln = QLineEdit()
        self.user_ln = QLineEdit()
        self.pass_ln = QLineEdit()
        self.pass_ln.setEchoMode(QLineEdit.Password)

        layout.addRow('Host:', self.host_ln)
        layout.addRow('User:', self.user_ln)
        layout.addRow('Pass:', self.pass_ln)

        main_params = get_main_window().params
        self.host_ln.setText(main_params['jira_host'])
        self.user_ln.setText(main_params['jira_user'])
        self.pass_ln.setText(main_params['jira_pass'])

        self.host_ln.textChanged.connect(get_main_window().update_start_button)
        self.user_ln.textChanged.connect(get_main_window().update_start_button)
        self.pass_ln.textChanged.connect(get_main_window().update_start_button)


class TasksFilterSettings(QGroupBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName('tasks_filter')
        self.setTitle('JIRA tasks filter settings')
        self.setAlignment(Qt.AlignHCenter)

        layout = QGridLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(5, 5, 5, 5)

        self.is_assignee = QCheckBox()
        self.is_validator = QCheckBox()
        self.is_creator = QCheckBox()

        self.is_assignee.setText('user is Assignee')
        self.is_validator.setText('user is Validator')
        self.is_creator.setText('user is Creator')

        layout.addWidget(self.is_assignee, 1, 0)
        layout.addWidget(self.is_validator, 2, 0)
        layout.addWidget(self.is_creator, 3, 0)

        main_params = get_main_window().params
        self.is_assignee.setChecked(main_params['tasks_filter']['user_assignee'])
        self.is_validator.setChecked(main_params['tasks_filter']['user_validator'])
        self.is_creator.setChecked(main_params['tasks_filter']['user_creator'])

        self.is_assignee.clicked.connect(get_main_window().update_start_button)
        self.is_validator.clicked.connect(get_main_window().update_start_button)
        self.is_creator.clicked.connect(get_main_window().update_start_button)


class DateSelector(QGroupBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName('dates_selector')
        self.setTitle('Dates range')
        self.setAlignment(Qt.AlignHCenter)

        self.layout = QHBoxLayout(self)
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # Setup 'From' selector
        from_frame = QFrame(self, Qt.Widget)
        from_layout = QVBoxLayout(from_frame)

        self.from_lbl = QLabel(from_frame)
        self.from_lbl.setText('Select From date')
        self.from_lbl.setStyleSheet('font: bold')

        self.from_cal = QCalendarWidget(from_frame)
        self.from_cal.setGridVisible(True)
        self.from_cal.setFirstDayOfWeek(Qt.DayOfWeek(1))
        self.from_cal.setMaximumDate(QDate().currentDate())
        self.from_cal.clicked.connect(self.update_calendars)
        self.from_cal.clicked.connect(get_main_window().update_start_button)

        from_layout.addWidget(self.from_lbl, 0, Qt.AlignHCenter)
        from_layout.addWidget(self.from_cal, 0, Qt.AlignHCenter)

        # Setup 'To' selector
        to_frame = QFrame(self, Qt.Widget)
        to_layout = QVBoxLayout(to_frame)

        self.to_lbl = QLabel(to_frame)
        self.to_lbl.setText('Select To date')
        self.to_lbl.setStyleSheet('font: bold')

        self.to_cal = QCalendarWidget(to_frame)
        self.to_cal.setGridVisible(True)
        self.to_cal.setFirstDayOfWeek(Qt.DayOfWeek(1))
        self.to_cal.setMaximumDate(QDate().currentDate())
        self.to_cal.clicked.connect(self.update_calendars)
        self.to_cal.clicked.connect(get_main_window().update_start_button)
        self.to_cal.setDisabled(True)

        to_layout.addWidget(self.to_lbl, 0, Qt.AlignHCenter)
        to_layout.addWidget(self.to_cal, 0, Qt.AlignHCenter)

        self.layout.addWidget(from_frame, 0, Qt.AlignCenter)
        self.layout.addWidget(to_frame, 0, Qt.AlignCenter)

        self.update_calendars()

    def update_calendars(self):
        if self.from_cal.selectedDate():
            self.to_cal.setEnabled(True)
            self.from_cal.setMaximumDate(QDate().currentDate())
            self.to_cal.setMinimumDate(self.from_cal.selectedDate())
            self.to_cal.setMaximumDate(QDate().currentDate())
            self.from_lbl.setText(self.from_cal.selectedDate().toString(Qt.ISODate))

        if self.to_cal.selectedDate():
            self.to_lbl.setText(self.to_cal.selectedDate().toString(Qt.ISODate))


class DaysConfigurator(QGroupBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.weekdays = WEEKDAYS
        self.weekday_switches = []
        self.setObjectName('days_config')
        self.setTitle('Working days settings')
        self.setAlignment(Qt.AlignHCenter)
        self.layout = QVBoxLayout(self)

        # Weekdays selector
        week_frame = QFrame(self, Qt.Widget)
        week_layout = QHBoxLayout(week_frame)
        week_layout.setSpacing(2)
        week_layout.setContentsMargins(0, 0, 0, 0)

        # Generating weekdays checkboxes
        for day, state in self.weekdays.items():
            checkbox = QCheckBox()
            checkbox.setText(day)
            checkbox.setChecked(state)
            checkbox.stateChanged.connect(self.update_weekdays)
            week_layout.addWidget(checkbox, 0, Qt.AlignHCenter)
            self.weekday_switches.append(checkbox)

        # Misc options
        misc_frame = QFrame(self, Qt.Widget)
        misc_layout = QFormLayout(misc_frame)
        misc_layout.setSpacing(5)
        misc_layout.setContentsMargins(0, 0, 0, 0)

        # Process daily tasks only control
        self.daily_only = QCheckBox()
        self.daily_only.setChecked(get_main_window().params['daily_only'])
        self.daily_only.setToolTip('If checked only Daily Tasks will be processed and logged\n'
                                   'Still they won\'t exceed target hours per day')

        # Target hours per day
        self.target_hrs = QDoubleSpinBox()
        self.target_hrs.setSingleStep(0.1)
        self.target_hrs.setDecimals(1)
        self.target_hrs.setRange(0, 24)
        self.target_hrs.setToolTip('Amount of working hours that logger will\nattempt to fill for each day.')
        self.target_hrs.setFixedWidth(50)
        self.target_hrs.setRange(1, 24)
        self.target_hrs.setValue(8)

        # Daily tasks
        tasks_frame = QFrame(self, Qt.Widget)
        tasks_layout = QFormLayout(tasks_frame)
        tasks_layout.setSpacing(5)
        tasks_layout.setContentsMargins(0, 0, 0, 0)
        self.daily_tasks = QLineEdit()
        regex = QRegExp('^[A-Z]+-[0-9]+:[0-9]+[smh]( [A-Z]+-[0-9]+:[0-9]+[smh])*$')  # BR-408:30m BR-7630:2h BR-2345:1h
        validator = QRegExpValidator(regex)
        self.daily_tasks.setValidator(validator)
        self.daily_tasks.textChanged.connect(self.validate_input)
        self.daily_tasks.setText(tasks_dict_to_string(get_main_window().params['daily_tasks']))
        self.daily_tasks.setToolTip('List of daily task:time that will be\nexplicitly logged for each day.\n'
                                    'Example: "BR-222:30m BR-555:1h"')

        # Tasks comment
        self.tasks_comment = QLineEdit()
        self.tasks_comment.setToolTip('Comment that will be added for every daily task')
        self.tasks_comment.setText(get_main_window().params['tasks_comment'])

        # Tasks to be ignored
        self.ignore_tasks = QLineEdit()
        regex = QRegExp('^[A-Z]+-[0-9]+( [A-Z]+-[0-9]+)*$')  # BR-408 BR-234 BR-7758
        validator = QRegExpValidator(regex)
        self.ignore_tasks.setValidator(validator)
        self.ignore_tasks.textChanged.connect(self.validate_input)
        self.ignore_tasks.setText(tasks_list_to_string(get_main_window().params['ignore_tasks']))
        self.ignore_tasks.setToolTip('List of tasks to be ignored during processing.\nExample: "BR-555 BR-777"')

        tasks_layout.addRow('Daily tasks', self.daily_tasks)
        tasks_layout.addRow('Comment', self.tasks_comment)
        tasks_layout.addRow('Ignore tasks', self.ignore_tasks)
        misc_layout.addRow('Process Daily Tasks only', self.daily_only)
        misc_layout.addRow('Target working hours per day:', self.target_hrs)

        # Placing sub-widgets to root layout
        self.layout.addWidget(week_frame, 0, Qt.AlignTop)
        self.layout.addWidget(tasks_frame, 0, Qt.AlignTop)
        self.layout.addWidget(misc_frame, 0, Qt.AlignTop)

    def update_weekdays(self):
        for switch in self.weekday_switches:
            self.weekdays[switch.text()] = switch.isChecked()

    def validate_input(self, *args, **kwargs):
        sender = self.sender()
        if not sender.text():
            sender.setStyleSheet('QLineEdit {background-color: "white"}')
            return

        validator = sender.validator()
        state = validator.validate(sender.text(), 0)[0]
        if state == validator.Acceptable:
            color = '#c4df9b'  # green
        else:
            color = '#fff79a'  # yellow
        sender.setStyleSheet('QLineEdit { background-color: %s }' % color)


class MainButtons(QWidget):
    def __init__(self, parent):
        super().__init__(parent, Qt.Widget)
        self.parent = parent
        self.setObjectName('main_buttons')

        layout = QHBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 5, 0, 0)

        self.start_btn = QPushButton('Start')
        self.start_btn.setFixedWidth(100)
        self.start_btn.clicked.connect(get_main_window().execute_autologging)

        layout.addWidget(self.start_btn, 0, Qt.AlignHCenter)


def get_main_window():
    """Get MainWindow object (root parent of all widgets)"""
    top_levels = qApp.topLevelWidgets()
    main = next((tl for tl in top_levels if (isinstance(tl, QMainWindow) and tl.objectName() == 'main_window')), None)
    return main


def tasks_string_to_dict(tasks_string: str):
    """Convert input string like 'BR-3452:5 BR-226:8' to common dict"""
    try:
        result = {k: v for k, v in [x.split(':') for x in tasks_string.split(' ') if x]} if tasks_string else {}
        return result
    except ValueError:
        return


def tasks_dict_to_string(tasks_dict: dict) -> str:
    return ' '.join([f'{k}:{v}' for k, v in list(tasks_dict.items())]) if tasks_dict else ''


def tasks_string_to_list(tasks_string: str) -> list:
    return [task for task in tasks_string.split(' ') if task] if tasks_string else []


def tasks_list_to_string(tasks_list: list) -> str:
    return ' '.join(tasks_list) if tasks_list else ''

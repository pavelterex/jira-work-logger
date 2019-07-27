from pathlib import Path

import yaml
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QMainWindow, QAction, qApp, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QSpinBox, QFrame,
                             QPushButton, QFormLayout, QLineEdit, QLabel, QCalendarWidget, QCheckBox, QGridLayout)

from ..constants import *
from ..log_worker import LogWorker


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setObjectName('main_window')
        self.menubar = self.menuBar()
        self.params = PARAMS
        self.load_config()
        self.init_ui()
        self.update_start_button()

    def init_ui(self):
        # Setting window geometry
        self.setContentsMargins(1, 1, 1, 1)
        self.setWindowTitle('JIRA work logger')
        self.setWindowIcon(QIcon('gui/misc/clock-icon.png'))

        # Setting menu bar
        app_menu = self.menubar.addMenu('App')  # File menu
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(qApp.quit)
        app_menu.addAction(exit_action)

        # Setting status bar
        self.statusBar().setSizeGripEnabled(True)
        self.statusBar().setStyleSheet('font-size: 10pt; font-family: Calibri; text-align: left; background: white;')

        # Setting root frame
        root = QWidget(self, Qt.Widget)
        root_layout = QVBoxLayout(root)

        # Setting widgets of main window
        root_layout.addWidget(UpperSettingsPanel(root), 0, Qt.AlignTop)
        root_layout.addWidget(DateSelector(root), 1, Qt.AlignTop)
        root_layout.addWidget(MainButtons(root), 0, Qt.AlignRight)

        # Displaying root as main widget
        self.setCentralWidget(root)

    def execute_autologging(self):
        self.read_params()
        LogWorker(self.params).execute_autologging()

    def update_start_button(self):
        self.read_params()
        start_btn = self.findChild(QWidget, 'main_buttons', Qt.FindChildrenRecursively).start_btn

        if not [param for param in MANDATORY_PARAMS if not self.params[param]]:
            start_btn.setEnabled(True)
            return

        start_btn.setDisabled(True)

    def read_params(self):
        # JIRA settings
        jira_widget = self.findChild(QWidget, 'jira_settings', Qt.FindChildrenRecursively)
        self.params['jira_host'] = jira_widget.host_ln.text()
        self.params['jira_user'] = jira_widget.user_ln.text()
        self.params['jira_pass'] = jira_widget.pass_ln.text()

        # Working days settings
        days_widget = self.findChild(QWidget, 'days_config', Qt.FindChildrenRecursively)
        self.params['work_days'] = days_widget.weekdays
        self.params['target_hrs'] = days_widget.target_hrs.value()
        self.params['daily_tasks'] = tasks_string_to_dict(days_widget.daily_tasks.text())

        # Date settings
        date_widget = self.findChild(QWidget, 'dates_selector', Qt.FindChildrenRecursively)
        self.params['from_date'] = date_widget.from_cal.selectedDate().toString(Qt.ISODate)
        self.params['to_date'] = date_widget.to_cal.selectedDate().toString(Qt.ISODate)

    def load_config(self):
        config_path = Path(CONFIG_FILE)

        if config_path.exists():
            self.params.update(yaml.load(config_path.read_text(), Loader=yaml.BaseLoader))
            return


class UpperSettingsPanel(QWidget):
    """Placeholder Frame for various settings widgets"""
    def __init__(self, parent):
        super().__init__(parent, Qt.Widget)
        self.parent = parent
        self.setObjectName('upper_settings')

        layout = QGridLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(JiraSettings(self), 0, 0)
        layout.addWidget(DaysConfigurator(self), 0, 1)


class JiraSettings(QGroupBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName('jira_settings')
        self.setTitle('JIRA settings')
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

        self.host_ln.setText(get_main_window().params['jira_host'])
        self.user_ln.setText(get_main_window().params['jira_user'])
        self.pass_ln.setText(get_main_window().params['jira_pass'])

        self.host_ln.textChanged.connect(get_main_window().update_start_button)
        self.user_ln.textChanged.connect(get_main_window().update_start_button)
        self.pass_ln.textChanged.connect(get_main_window().update_start_button)


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
        self.to_cal.clicked.connect(self.update_calendars)
        self.to_cal.clicked.connect(get_main_window().update_start_button)
        self.to_cal.setDisabled(True)

        to_layout.addWidget(self.to_lbl, 0, Qt.AlignHCenter)
        to_layout.addWidget(self.to_cal, 0, Qt.AlignHCenter)

        # Placing selectors to root layout
        self.layout.addWidget(from_frame, 0, Qt.AlignCenter)
        self.layout.addWidget(to_frame, 0, Qt.AlignCenter)

    def update_calendars(self):
        if self.from_cal.selectedDate():
            self.to_cal.setEnabled(True)
            self.to_cal.setMinimumDate(self.from_cal.selectedDate())
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

        self.target_hrs = QSpinBox()
        self.target_hrs.setFixedWidth(50)
        self.target_hrs.setRange(1, 24)
        self.target_hrs.setValue(8)

        self.daily_tasks = QLineEdit()

        misc_layout.addRow('Target working hours per day:', self.target_hrs)
        misc_layout.addRow('Daily tasks (task:time task:time)', self.daily_tasks)
        self.daily_tasks.setText(tasks_dict_to_string(get_main_window().params['daily_tasks']))

        # Placing sub-widgets to root layout
        self.layout.addWidget(week_frame, 0, Qt.AlignTop)
        self.layout.addWidget(misc_frame, 0, Qt.AlignTop)

    def update_weekdays(self):
        for switch in self.weekday_switches:
            self.weekdays[switch.text()] = switch.isChecked()


class MainButtons(QWidget):
    def __init__(self, parent):
        super().__init__(parent, Qt.Widget)
        self.parent = parent
        self.setObjectName('main_buttons')

        layout = QHBoxLayout(self)
        layout.setSpacing(3)
        layout.setContentsMargins(3, 3, 3, 3)

        self.start_btn = QPushButton('Start')
        self.start_btn.setFixedWidth(100)
        self.start_btn.clicked.connect(get_main_window().execute_autologging)

        layout.addWidget(self.start_btn, 0, Qt.AlignHCenter)


def get_main_window():
    """Get MainWindow object (root parent of all widgets)"""
    top_levels = qApp.topLevelWidgets()
    main = next((tl for tl in top_levels if (isinstance(tl, QMainWindow) and tl.objectName() == 'main_window')), None)
    return main


def tasks_string_to_dict(tasks_string: str) -> dict:
    """Convert input string like 'BR-3452:5 BR-226:8' to common dict"""
    return {k: v for k, v in [x.split(':') for x in tasks_string.split(' ') if x]}


def tasks_dict_to_string(tasks_dict: dict) -> str:
    """Convert input dict to string of daily tasks"""
    return ' '.join([f'{k}:{v}' for k, v in list(tasks_dict.items())])

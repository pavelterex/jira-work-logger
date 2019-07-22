from PyQt5.QtCore import Qt, QRegExp, QDate
from PyQt5.QtGui import QIcon, QCursor, QRegExpValidator
from PyQt5.QtWidgets import (QMainWindow, QAction, qApp, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QScrollArea,
                             QFrame, QListWidget, QPushButton, QFormLayout, QLineEdit, QComboBox, QMessageBox, QLabel,
                             QTextBrowser, QFileDialog, QTableWidget, QCalendarWidget, QTableWidgetItem,
                             QAbstractItemView, QHeaderView)
from jira import JIRA


APP_VERSION = '0.1'
APP_CONFIG = {
    'jira_host': '',
    'jira_user': '',
    'jira_pass': ''
}


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Window)
        self.setObjectName('main_window')
        self.menubar = self.menuBar()
        self.config = APP_CONFIG
        self.init_ui()

    def init_ui(self):
        # Setting window geometry
        self.setContentsMargins(1, 1, 1, 1)
        self.setWindowTitle('JIRA work logger')
        # self.setWindowIcon(QIcon('misc/projectavatar.ico'))

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
        root_layout.addWidget(JiraSettings(root), 0, Qt.AlignTop)
        root_layout.addWidget(DatesSelector(root), 1, Qt.AlignTop)
        # root_layout.addWidget(RequestsManager(root), 1, Qt.AlignTop)
        # root_layout.addWidget(UsageNotificationLabel(root), 0, Qt.AlignCenter)

        # Displaying root as main widget
        self.setCentralWidget(root)

    # def launch_settings_editor(self):
    #     SettingsEditor(self, self.loaded_config).show()

    # def save_loaded_config(self):
    #     yaml.dump(self.loaded_config, SETTINGS_FILE.open('w'), default_flow_style=False)
    #     self.statusBar().showMessage('Settings successfully saved', 5000)


class JiraSettings(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setObjectName('jira_settings')
        self.setTitle('JIRA settings')
        self.setAlignment(Qt.AlignHCenter)

        self.layout = QFormLayout(self)
        self.layout.setSpacing(3)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setLabelAlignment(Qt.AlignRight)

        self.host_ln = QLineEdit()
        self.user_ln = QLineEdit()
        self.pass_ln = QLineEdit()
        self.pass_ln.setEchoMode(QLineEdit.Password)
        # self.test_btn = QPushButton('Test connection')
        # self.test_btn.clicked.connect()

        self.layout.addRow('Host:', self.host_ln)
        self.layout.addRow('User:', self.user_ln)
        self.layout.addRow('Pass:', self.pass_ln)
        # self.layout.addRow('', self.test_btn)


class DatesSelector(QGroupBox):
    def __init__(self, parent=None):
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

        self.from_cal = QCalendarWidget(from_frame)
        self.from_cal.setGridVisible(True)
        self.from_cal.clicked.connect(lambda x: self.show_date(self.from_lbl, self.from_cal))

        from_layout.addWidget(self.from_cal, 0, Qt.AlignHCenter)
        from_layout.addWidget(self.from_lbl, 0, Qt.AlignHCenter)

        # Setup 'To' selector
        to_frame = QFrame(self, Qt.Widget)
        to_layout = QVBoxLayout(to_frame)

        self.to_lbl = QLabel(to_frame)
        self.to_lbl.setText('Select To date')

        self.to_cal = QCalendarWidget(to_frame)
        self.to_cal.setGridVisible(True)
        self.to_cal.clicked.connect(lambda x: self.show_date(self.to_lbl, self.to_cal))

        to_layout.addWidget(self.to_cal, 0, Qt.AlignHCenter)
        to_layout.addWidget(self.to_lbl, 0, Qt.AlignHCenter)

        # Placing selectors to root layout
        self.layout.addWidget(from_frame, 0, Qt.AlignCenter)
        self.layout.addWidget(to_frame, 0, Qt.AlignCenter)

    @staticmethod
    def show_date(label, cal):
        date = cal.selectedDate()
        label.setText(date.toString())


def get_main_window():
    """Get MainWindow object (root parent of all widgets)"""
    top_levels = qApp.topLevelWidgets()
    main = next((tl for tl in top_levels if (isinstance(tl, QMainWindow) and tl.objectName() == 'main_window')), None)
    return main

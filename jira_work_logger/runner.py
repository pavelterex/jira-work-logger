import sys

from PyQt5.QtWidgets import QApplication

from jira_work_logger.gui.widgets import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    root = MainWindow()
    root.setContentsMargins(3, 3, 3, 3)
    root.show()
    app.exec_()

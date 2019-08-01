import os
import re
import shutil
from pathlib import Path

DLLS_NOT_TO_MOVE = re.compile('((^python.+)|(^VCRUNTIME.+)|(^MSVCP.+)|(^pywintypes.+)|(^Qt5.+)|(^sqlite.+))')

if __name__ == '__main__':
    os.system('pyinstaller setup.spec --clean --noconfirm')

    root = Path(Path(__file__).parent, 'dist\\Jira Work Logger')

    lib = Path(root, 'lib')
    lib.mkdir(parents=True, exist_ok=True)

    windll = Path(root, 'windll')
    windll.mkdir(parents=True, exist_ok=True)

    all_files = list(root.iterdir())
    pyd_files = [file_ for file_ in all_files if file_.is_file() and file_.suffix == '.pyd']
    dll_files = [file_ for file_ in all_files if
                 file_.is_file() and file_.suffix == '.dll'and not DLLS_NOT_TO_MOVE.match(file_.stem)]

    for file_ in pyd_files:
        shutil.move(str(file_), str(lib))

    for file_ in dll_files:
        shutil.move(str(file_), str(windll))

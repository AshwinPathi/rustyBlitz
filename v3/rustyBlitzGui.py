from PyQt6.QtWidgets import QComboBox, QMainWindow, QApplication, QWidget, QVBoxLayout, QPushButton, QTextEdit
from PyQt6.QtGui import QIcon, QTextCursor
import sys
import config
from utils import initialize_league_location, strip_punctuation
from rune_selector import RuneSelector
import time
import atexit

def get_champions():
    return [key for key in config.CHAMP_DATA["name_to_id"]]

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.init_geometry()
        self.init_ui()
        self.init_rune_selector()

    def init_geometry(self):
        self.setGeometry(100, 100, 300, 300)

    def init_ui(self):
        self.champ_combo_box = QComboBox()
        self.champ_combo_box.addItems(get_champions())

        self.role_combo_box = QComboBox()
        self.role_combo_box.addItems(config.ROLES)

        self.backend_combo_box = QComboBox()
        self.backend_combo_box.addItems(config.BACKENDS)

        self.submit_button = QPushButton('Get Runes')
        self.submit_button.clicked.connect(self.get_selection)

        # https://stackoverflow.com/questions/16568451/pyqt-how-to-make-a-textarea-to-write-messages-to-kinda-like-printing-to-a-co
        self.logOutput = QTextEdit()
        self.logOutput.setReadOnly(True)
        self.font = self.logOutput.font()
        self.font.setFamily("Courier")
        self.font.setPointSize(10)

        layout = QVBoxLayout()
        layout.addWidget(self.champ_combo_box)
        layout.addWidget(self.role_combo_box)
        layout.addWidget(self.backend_combo_box)
        layout.addWidget(self.submit_button)
        layout.addWidget(self.logOutput)

        container = QWidget()
        container.setLayout(layout)
        self.setWindowTitle('RustyBlitz')
        self.setCentralWidget(container)
        
    def init_rune_selector(self):
        lockfile_data = initialize_league_location()
        self.rs = RuneSelector(lockfile_data)

    def _populate_runes(self, champ, role, backend, dry_run, use_cache):
        resp = self.rs.populate_runes(champ, role, backend=backend, dry_run=dry_run, use_cache=use_cache)

    def get_selection(self):
        champ = self.champ_combo_box.currentText()
        role = self.role_combo_box.currentText()
        backend = strip_punctuation(self.backend_combo_box.currentText()).lower()
        dry_run = False
        use_cache = True

        self.logOutput.insertPlainText("Getting runes for: {} {}\n".format(champ, role))
        sb = self.logOutput.verticalScrollBar()
        sb.setValue(sb.maximum())

        start = time.time()
        self._populate_runes(champ, role, backend, dry_run, use_cache)
        end = time.time()

        self.logOutput.insertPlainText("Populated runes in {:.7f} seconds\n\n".format(end-start))
        sb = self.logOutput.verticalScrollBar()
        sb.setValue(sb.maximum())

def exit_handler():
    print("writing cache to disk")
    config.RUNE_CACHE._write_to_disk()

if __name__ == "__main__":
    atexit.register(exit_handler)
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
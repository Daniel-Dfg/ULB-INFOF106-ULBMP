"""
NOM : DEFOING
PRÉNOM : Daniel
SECTION : INFO
MATRICULE : 000589910
"""

from sys import exit
from window import MainWindow
from PySide6.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    exit(app.exec())
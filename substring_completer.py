import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QVBoxLayout, QComboBox, QApplication, QCompleter)
from PyQt5.QtCore import Qt, QStringListModel
import csv
import os

class SubstringCompleter(QCompleter):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setCompletionMode(QCompleter.PopupCompletion)
        self.setFilterMode(Qt.MatchContains)
        self.model = QStringListModel(items, self)
        self.setModel(self.model)

    def pathFromIndex(self, index):
        return self.model.data(index, Qt.DisplayRole)

class PDFViewer(QMainWindow):
    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.student_list = self.load_students_from_csv("students.csv")
        self.setWindowTitle("Academic Records Manager")
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        student_label = QLabel("Student Name:")
        self.layout.addWidget(student_label)

        self.student_combo = QComboBox()
        self.student_combo.setEditable(True)

        # Initialize SubstringCompleter with the list of students
        self.student_completer = SubstringCompleter(self.student_list, self.student_combo)
        self.student_combo.setCompleter(self.student_completer)
        self.student_combo.addItems(self.student_list)

        # Connect signals to slots
        self.student_combo.activated[str].connect(self.on_student_selected)
        self.student_completer.activated.connect(self.on_completion_selected)

        self.layout.addWidget(self.student_combo)

    def load_students_from_csv(self, file_path):
        students = []
        if os.path.exists(file_path):
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    students.append(row['student_name'])
        return students

    def on_student_selected(self, text):
        # Update the combo box text with the selected item
        self.student_combo.setCurrentText(text)

    def on_completion_selected(self, index):
        # Ensure the selected item from completer is shown in the combo box
        selected_student = self.student_completer.model.data(index, Qt.DisplayRole)
        self.student_combo.setCurrentText(selected_student)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFViewer()
    window.show()
    sys.exit(app.exec_())

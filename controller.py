from model import AcademicRecordsModel
from viewTry import PDFViewer
import os
from PyQt5.QtCore import QDate

class PDFController:
    def __init__(self):
        self.model = AcademicRecordsModel()
        self.view = PDFViewer(self)
        self.load_config()
        self.set_default_values()

    def load_config(self):
        
        date_given_str = self.model.get_config("date_given")
        date_graded_str = self.model.get_config("date_graded")

        if date_given_str:
            date_given = QDate.fromString(date_given_str, "yyyy-MM-dd")
            if date_given.isValid():
                self.view.date_given_entry.setDate(date_given)
            else:
                self.view.date_given_entry.setDate(QDate.currentDate())
        else:
            self.view.date_given_entry.setDate(QDate.currentDate())

        if date_graded_str:
            # date_graded = QDate.fromString(date_graded_str, "yyyy-MM-dd")
            date_graded = QDate.currentDate()
            if date_graded.isValid():
                self.view.date_graded_entry.setDate(date_graded)
            else:
                self.view.date_graded_entry.setDate(QDate.currentDate())
        else:
            self.view.date_graded_entry.setDate(QDate.currentDate())

    def save_config(self):
        # self.model.set_config("course", self.view.course_entry.text())
        # self.model.set_config("activity_name", self.view.activity_entry.text())
        self.model.set_config("date_given", self.view.date_given_entry.date().toString("yyyy-MM-dd"))
        self.model.set_config("date_graded", self.view.date_graded_entry.date().toString("yyyy-MM-dd"))

    def save_to_database_and_pdf(self):
        self.view.save_to_database_and_pdf()

    def set_default_values(self):
        # default_course = "Course 101"
        # default_activity = "Quiz 1"
        default_date_given = QDate(2024, 6, 13)
        default_date_graded = QDate.currentDate()

        # self.model.set_config("course", default_course)
        # self.model.set_config("activity_name", default_activity)
        self.model.set_config("date_given", default_date_given.toString("yyyy-MM-dd"))
        self.model.set_config("date_graded", default_date_graded.toString("yyyy-MM-dd"))

        # self.view.course_entry.setText(default_course)
        # self.view.activity_entry.setText(default_activity)
        self.view.date_given_entry.setDate(default_date_given)
        self.view.date_graded_entry.setDate(default_date_graded)

    def run(self):
        self.view.show()

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    controller = PDFController()
    controller.run()
    sys.exit(app.exec_())

import sys
from PyQt5.QtWidgets import (QMainWindow,QSlider, QWidget, QLabel, QPushButton, QLineEdit, 
                             QTextEdit, QMessageBox, QVBoxLayout, QScrollArea, QSizePolicy, 
                             QDateEdit, QFileDialog, QDialog, QDialogButtonBox, QFormLayout, QComboBox, QMenuBar, QAction,QSplitter)
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import Qt, QDate
import fitz  # PyMuPDF
import os
import json
import csv
import sqlite3
from PIL import Image
import pandas as pd  # Import pandas for Excel export
from substring_completer import SubstringCompleter  # Use relative import
from pdf_comment_generator import MathPDFGenerator

CONFIG_FILE = "config.json"
STUDENTS_CSV = "students.csv"  # Adjust path if necessary

class PDFViewer(QMainWindow):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.session_data = {
            "course": "",
            "activity_name": ""
        }

        self.student_list = self.load_students_from_csv(STUDENTS_CSV)

        self.setWindowTitle("Academic Records Manager")
        self.setGeometry(0, 0, 1200, 700)

        self.init_ui()
        self.init_db()

        self.load_config()  # Load the course and activity names
        self.prompt_for_course_and_activity()

    def init_ui(self):
        self.create_menu_bar()

        pdf_viewer_container = QWidget()
        pdf_layout = QVBoxLayout()
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setMinimumWidth(500)
        self.scroll_area.setMinimumHeight(250)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.pdf_layout = QVBoxLayout()
        self.scroll_widget = QWidget()
        self.scroll_widget.setLayout(self.pdf_layout)
        self.scroll_area.setWidget(self.scroll_widget)
        pdf_layout.addWidget(self.scroll_area)
        pdf_viewer_container.setLayout(pdf_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout()

        browse_button = QPushButton("Browse PDF")
        browse_button.clicked.connect(self.browse_files)
        right_layout.addWidget(browse_button)

        grade_label = QLabel("Grade:")
        right_layout.addWidget(grade_label)
        self.grade_entry = QLineEdit()
        right_layout.addWidget(self.grade_entry)

        date_given_label = QLabel("Date Activity Given:")
        right_layout.addWidget(date_given_label)
        self.date_given_entry = QDateEdit()
        self.date_given_entry.setCalendarPopup(True)
        self.date_given_entry.setDate(QDate.currentDate())
        right_layout.addWidget(self.date_given_entry)

        date_graded_label = QLabel("Date Graded:")
        right_layout.addWidget(date_graded_label)
        self.date_graded_entry = QDateEdit()
        self.date_graded_entry.setCalendarPopup(True)
        self.date_graded_entry.setDate(QDate.currentDate())
        right_layout.addWidget(self.date_graded_entry)

        input_label = QLabel("Selected PDF:")
        right_layout.addWidget(input_label)
        self.input_entry = QLineEdit()
        self.input_entry.setReadOnly(True)  # Make it read-only since it's set by the browse button
        right_layout.addWidget(self.input_entry)

        student_label = QLabel("Student Name:")
        right_layout.addWidget(student_label)
        self.student_combo = QComboBox()
        self.student_combo.setEditable(True)
        self.student_completer = SubstringCompleter(self.student_list, self.student_combo)
        self.student_completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.student_combo.setCompleter(self.student_completer)
        self.student_combo.addItems(self.student_list)
        self.student_combo.activated[str].connect(self.on_student_selected) # Handle selection
        right_layout.addWidget(self.student_combo)

        comment_label = QLabel("Comment:")
        right_layout.addWidget(comment_label)
        self.comment_entry = QTextEdit()
        self.comment_entry.setFont(QFont('Arial', 20))
        right_layout.addWidget(self.comment_entry)

        add_button = QPushButton("Save to Database and PDF")
        add_button.clicked.connect(self.controller.save_to_database_and_pdf)
        right_layout.addWidget(add_button)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(self.clear_fields)
        right_layout.addWidget(clear_button)

        right_widget.setLayout(right_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(pdf_viewer_container)
        splitter.addWidget(right_widget)

        splitter.setSizes([700, 500])  # Adjusted sizes as we removed the directory tree

        container_layout = QVBoxLayout()
        container_layout.addWidget(splitter)
        container_widget = QWidget()
        container_widget.setLayout(container_layout)
        self.setCentralWidget(container_widget)

        # Adding Zoom Slider
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setMinimum(1)
        self.zoom_slider.setMaximum(5)
        self.zoom_slider.setValue(1)
        self.zoom_slider.setTickPosition(QSlider.TicksBelow)
        self.zoom_slider.setTickInterval(1)
        self.zoom_slider.valueChanged.connect(self.zoom_changed)
        right_layout.addWidget(self.zoom_slider)

    def create_menu_bar(self):
        menubar = QMenuBar(self)
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu("File")

        export_action = QAction("Database Export to Excel", self)
        export_action.triggered.connect(self.export_to_excel)
        file_menu.addAction(export_action)

        # Add submenu for exporting comments
        export_comments_action = QAction("Export Comments to Excel",self)
        export_comments_action.triggered.connect(self.export_comments_to_excel)
        file_menu.addAction(export_comments_action)
    
    def export_comments_to_excel(self):
         save_path, _ = QFileDialog.getSaveFileName(self, "Save Comments to Excel", "", "Excel Files (*.xlsx);;All Files (*)")
         if save_path:
            try:
                self.write_comments_to_excel(save_path)
                QMessageBox.information(self, "Success", "Comments exported to Excel successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export comments: {e}")

    def write_comments_to_excel(self, file_path):
        # Connect to the database
        conn = sqlite3.connect('academic_records.db')

        # Read the comments from the database into a pandas DataFrame
        query = """
        SELECT student_name, course, activity_name, comment
        FROM Records
        WHERE comment IS NOT NULL AND comment != ''
        """
        df = pd.read_sql_query(query, conn)

        # Pivot the DataFrame to have activities as columns and comments as values
        pivoted_df = df.pivot_table(index=['student_name'], 
                                    columns=['activity_name'], 
                                    values='comment', 
                                    aggfunc='first')  # Use 'first' to get the first occurrence of a comment per student-activity

        # Rename columns for clarity
        pivoted_df.columns = [f'Comment_{col}' for col in pivoted_df.columns]

        # Reset the index to make 'student_name' a column again
        pivoted_df.reset_index(inplace=True)

        # Write the DataFrame to an Excel file
        pivoted_df.to_excel(file_path, index=False, engine='openpyxl')

        # Close the database connection
        conn.close()

    def load_students_from_csv(self, file_path):
        students = []
        if os.path.exists(file_path):
            with open(file_path, newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    students.append(row['student_name'])
        else:
            print(f"CSV file not found: {file_path}")
        return students
    
    def on_student_selected(self,text):
        self.student_combo.setCurrentText

    def browse_files(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF File", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if file_path:
            self.input_entry.setText(file_path)
            self.display_original(file_path)

    def display_original(self, pdf_path,zoom_factor=1):
        for i in reversed(range(self.pdf_layout.count())):
            self.pdf_layout.itemAt(i).widget().deleteLater()

        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom_factor,zoom_factor))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = img.convert("RGBA")

            qim = QImage(img.tobytes("raw", "RGBA"), img.width, img.height, QImage.Format_ARGB32)
            pixmap = QPixmap.fromImage(qim)

            label = QLabel()
            label.setPixmap(pixmap)
            self.pdf_layout.addWidget(label)

    def clear_fields(self):
        self.grade_entry.clear()
        self.input_entry.clear()
        self.student_combo.setCurrentIndex(-1)  # Clear the combo box selection
        self.comment_entry.clear()
        self.clear_pdf_viewer()
        self.zoom_slider.setValue(1)

    def clear_pdf_viewer(self):
        for i in reversed(range(self.pdf_layout.count())):
            self.pdf_layout.itemAt(i).widget().deleteLater()

    def init_db(self):
        self.conn = sqlite3.connect('academic_records.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_name TEXT,
                course TEXT,
                activity_name TEXT,
                grade TEXT,
                date_given TEXT,
                date_graded TEXT,
                comment TEXT
            )
        ''')
        self.conn.commit()

    def save_to_database_and_pdf(self):
        course = self.session_data["course"]
        activity_name = self.session_data["activity_name"]
        grade = self.grade_entry.text()
        date_given = self.date_given_entry.date().toString("yyyy-MM-dd")
        date_graded = self.date_graded_entry.date().toString("yyyy-MM-dd")
        comment = self.comment_entry.toPlainText()
        input_path = self.input_entry.text()
        student_name = self.student_combo.currentText()

        if not input_path or not student_name:
            QMessageBox.warning(self, "Error", "Please select a PDF and specify a student name.")
            return
        if not os.path.isfile(input_path):
            QMessageBox.warning(self, "Error", f"The file {input_path} does not exist.")
            return

        # Sanitize student name by removing spaces and commas
        sanitized_student_name = student_name.replace(" ", "_").replace(",", "")

        input_folder = os.path.dirname(input_path)
        new_folder = os.path.join(os.path.dirname(input_folder), sanitized_student_name)

        if os.path.exists(new_folder):
            QMessageBox.warning(self, "Error", f"The folder {new_folder} already exists. Please choose a different name.")
            return

        try:
            os.rename(input_folder, new_folder)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to rename folder: {e}")
            return

        new_input_path = os.path.join(new_folder, os.path.basename(input_path))
        output_path = os.path.join(new_folder, sanitized_student_name + ".pdf")



        try:
            self.add_math_image_to_pdf(new_input_path, output_path, comment)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to modify PDF: {e}")
            return

        self.cursor.execute('''
            INSERT INTO Records (student_name, course, activity_name, grade, date_given, date_graded, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (student_name, course, activity_name, grade, date_given, date_graded, comment))

        self.conn.commit()
        QMessageBox.information(self, "Success", "Record saved to database and PDF modified.")

    def add_math_image_to_pdf(self, input_path, output_path, latex_code):
        if not os.path.isfile(input_path):
            QMessageBox.warning(self, "Error", f"Input file not found: {input_path}")
            return

        # Create an image from the LaTeX code
        math_pdf_gen = MathPDFGenerator()
        pdf_path = math_pdf_gen.create_pdf_from_latex(latex_code)

        if not pdf_path:
            QMessageBox.warning(self, "Error", "Failed to create pdf from LaTeX code.")
            return

        try:
            print(f"Attempting to open PDF file at {input_path}")
            original_doc = fitz.open(input_path)
            print(f"Successfully opened PDF file: {input_path}")

            print(f"Attempting to open PDF file at {pdf_path}")
            comment_pdf = fitz.open(pdf_path)
            print(f"Successfully opened PDF file: {pdf_path}")

            # Create a new document to combine both
            new_doc = fitz.open()
            new_doc.insert_pdf(original_doc)
            new_doc.insert_pdf(comment_pdf)

            # Save the combined PDF to the output path
            new_doc.save(output_path)
            print(f"Saved new PDF file to: {output_path}")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to modify PDF: {e}")
            print(f"Error encountered: {e}")
        finally:
            # Ensure files are closed to prevent any resource leak
            try:
                if 'new_doc' in locals():
                    new_doc.close()
                if 'original_doc' in locals():
                    original_doc.close()
                if 'image_doc' in locals():
                    comment_pdf.close()
            except Exception as close_error:
                print(f"Error while closing documents: {close_error}")

            # Cleanup: Remove the generated image file
            if os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                    print(f"Removed temporary image file: {pdf_path}")
                except Exception as remove_error:
                    print(f"Failed to remove temporary image file: {remove_error}")



    def export_to_excel(self):
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Excel File", "", "Excel Files (*.xlsx);;All Files (*)")
        if save_path:
            try:
                self.write_db_to_excel(save_path)
                QMessageBox.information(self, "Success", "Database exported to Excel successfully.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to export database: {e}")

    def write_db_to_excel(self, file_path):
        # Connect to the database
        conn = sqlite3.connect('academic_records.db')

        # Read the database table into a pandas DataFrame
        df = pd.read_sql_query("SELECT * FROM Records", conn)

        # Convert the 'grade' column to numeric type, handling any errors
        df['grade']=pd.to_numeric(df['grade'],errors='coerce')

        # Write the DataFrame to an Excel file
        df.to_excel(file_path, index=False, engine='openpyxl')

        # Close the database connection
        conn.close()

    def prompt_for_course_and_activity(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Set Course and Activity Name")

        form_layout = QFormLayout(dialog)
        course_input = QLineEdit(dialog)
        activity_input = QLineEdit(dialog)

        course_input.setText(self.session_data["course"])
        activity_input.setText(self.session_data["activity_name"])

        form_layout.addRow("Course:", course_input)
        form_layout.addRow("Activity Name:", activity_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        form_layout.addWidget(button_box)

        if dialog.exec_() == QDialog.Accepted:
            self.session_data["course"] = course_input.text()
            self.session_data["activity_name"] = activity_input.text()

        self.update_title_and_fields()
        self.save_config()  # Save the updated names to config

    def update_title_and_fields(self):
        course = self.session_data["course"]
        activity_name = self.session_data["activity_name"]
        self.setWindowTitle(f"Academic Records Manager - {course} | {activity_name}")

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as file:
                try:
                    config = json.load(file)
                    self.session_data["course"] = config.get("course", "")
                    self.session_data["activity_name"] = config.get("activity_name", "")
                except json.JSONDecodeError:
                    print("Error reading config file. Using default values.")

    def save_config(self):
        with open(CONFIG_FILE, 'w') as file:
            config = {
                "course": self.session_data["course"],
                "activity_name": self.session_data["activity_name"]
            }
            json.dump(config, file)

    # This is the zoom for the pdf in the pdf viewer
    def zoom_changed(self):
        zoom_factor = self.zoom_slider.value()
        self.display_original(self.input_entry.text(),zoom_factor)


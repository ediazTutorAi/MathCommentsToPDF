# pdf_solution_handler.py
import fitz  # PyMuPDF
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class PDFSolutionHandler:
    def __init__(self):
        self.solution_pdf_path = None

    def prompt_for_solution_pdf(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        file_path, _ = QFileDialog.getOpenFileName(None, "Select Solutions PDF", "", "PDF Files (*.pdf);;All Files (*)", options=options)
        if file_path:
            self.solution_pdf_path = file_path
        return self.solution_pdf_path

    def merge_with_solution_pdf(self, original_pdf_path, comment_pdf_path, output_pdf_path):
        try:
            new_doc = fitz.open()  # Create a new document for the merged content

            # We had a problem because we were inserting the original 
            # pdf with the other ones that already had the original 
            # pdf in it ChatGpt didn't realize that, obviously.
            
            # Insert the comments PDF
            with fitz.open(comment_pdf_path) as comment_pdf:
                new_doc.insert_pdf(comment_pdf)

            # Insert the solutions PDF if selected
            if self.solution_pdf_path:
                with fitz.open(self.solution_pdf_path) as solution_pdf:
                    new_doc.insert_pdf(solution_pdf)

            # Save the combined document
            new_doc.save(output_pdf_path)
            QMessageBox.information(None, "Success", f"PDFs merged and saved to {output_pdf_path}")

        except Exception as e:
            QMessageBox.warning(None, "Error", f"Failed to merge PDFs: {e}")
        finally:
            new_doc.close()  # Ensure the new document is closed properly

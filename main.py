from controller import PDFController
import sys
from PyQt5.QtWidgets import QApplication

if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = PDFController()
    controller.run()
    sys.exit(app.exec_())

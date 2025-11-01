
# insights.py

from PyQt6.QtWidgets import QWidget, QApplication, QPushButton, QVBoxLayout, QTextEdit, QProgressBar, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
import sys
import json
import requests

class InsightsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('AI Insights')

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_edit.setAcceptRichText(False)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setOrientation(Qt.Horizontal)
        self.progress_bar.setVisible(False)

        refresh_button = QPushButton('Refresh', self)
        refresh_button.clicked.connect(self.refresh_insights)

        layout = QVBoxLayout()
        layout.addWidget(self.text_edit)
        layout.addWidget(self.progress_bar)
        layout.addWidget(refresh_button)
        self.setLayout(layout)

    def refresh_insights(self):
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        manager = QNetworkAccessManager(self)
        request = QNetworkRequest(QUrl("http://127.0.0.1:8000/insights"))
        self.progress_bar.setMaximum(100)

        def update_progress(bytes_so_far, total_bytes):
            progress = int(bytes_so_far * 100 / total_bytes)
            self.progress_bar.setValue(progress)

        manager.get(request).finished.connect(lambda: self.handle_response(update_progress))
        manager.get(request).downloadProgress.connect(update_progress)

    def handle_response(self, update_progress):
        self.progress_bar.setVisible(False)
        try:
            response = requests.get("http://127.0.0.1:8000/insights")
            response.raise_for_status()
            insights_data = response.json()
            self.text_edit.setText(insights_data.get('summary', 'No insights available'))
        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Error", f"Failed to fetch insights: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = InsightsWidget()
    widget.show()
    sys.exit(app.exec())


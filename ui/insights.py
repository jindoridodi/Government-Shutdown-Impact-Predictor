from PyQt6.QtWidgets import QWidget, QApplication, QPushButton, QVBoxLayout, QTextEdit, QProgressBar, QMessageBox
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest
import sys
import json

class InsightsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.manager = QNetworkAccessManager(self)  # keep it as an attribute
        self.initUI()

    def initUI(self):
        self.setWindowTitle('AI Insights')

        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        self.text_edit.setLineWrapMode(QTextEdit.WidgetWidth)
        self.text_edit.setAcceptRichText(False)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setOrientation(Qt.Orientation.Horizontal)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)

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

        url = QUrl("http://127.0.0.1:8000/insights")
        request = QNetworkRequest(url)

        reply = self.manager.get(request)  # single request

        # progress
        reply.downloadProgress.connect(self._on_download_progress)
        # finished
        reply.finished.connect(lambda r=reply: self._handle_response(r))

    def _on_download_progress(self, bytes_received: int, bytes_total: int):
        if bytes_total > 0:
            self.progress_bar.setValue(int(bytes_received * 100 / bytes_total))
        else:
            # unknown total size; show indeterminate
            self.progress_bar.setRange(0, 0)

    def _handle_response(self, reply):
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)

        # Check for network errors
        if reply.error():
            QMessageBox.critical(self, "Error", f"Failed to fetch insights: {reply.errorString()}")
            reply.deleteLater()
            return

        try:
            data_bytes = reply.readAll().data()
            payload = json.loads(data_bytes.decode("utf-8"))
            self.text_edit.setPlainText(payload.get("summary", "No insights available"))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Invalid response: {e}")
        finally:
            reply.deleteLater()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = InsightsWidget()
    widget.show()
    sys.exit(app.exec())


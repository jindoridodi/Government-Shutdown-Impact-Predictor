
# main.py

import os
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QPushButton,
    QFileDialog,
    QLabel
)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtWebEngineWidgets import QWebEngineView
import requests
import pandas as pd
import folium
from folium import plugins
import plotly.graph_objs as go

# Assuming FastAPI backend is running on http://localhost:8000
FASTAPI_BASE_URL = "http://localhost:8000/api"

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        self.map_view = QWebEngineView()
        self.load_heatmap()
        self.layout.addWidget(self.map_view)
        self.setLayout(self.layout)

    def load_heatmap(self):
        # Load data from CSV and create heatmap using Folium
        base_dir = os.path.dirname(__file__)
        csv_path = os.path.join(base_dir, "data", "processed", "regional_risk.csv")
        data = pd.read_csv(csv_path)
        m = folium.Map(location=[37.7749, -122.4194], zoom_start=12)  # Example coordinates and zoom
        plugins.HeatMap(data[['lat', 'lon', 'risk_score']].values).add_to(m)
        self.map_view.setHtml(m.get_root().render())

class Analytics(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        # Placeholder for Plotly graph initialization
        self.layout.addWidget(QLabel("Analytics Tab - Placeholder for Plotly graphs"))
        self.setLayout(self.layout)

class Insights(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()
        # Placeholder for watsonx.ai summaries
        self.layout.addWidget(QLabel("Insights Tab - Placeholder for watsonx.ai summaries"))
        self.setLayout(self.layout)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Predictive Risk Dashboard')
        self.setGeometry(100, 100, 800, 600)

        self.tab_widget = QTabWidget()
        self.tab_widget.setGeometry(QRect(10, 10, 780, 580))

        self.dashboard_tab = Dashboard()
        self.analytics_tab = Analytics()
        self.insights_tab = Insights()

        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.addTab(self.analytics_tab, "Analytics")
        self.tab_widget.addTab(self.insights_tab, "Insights")

        self.setCentralWidget(self.tab_widget)

        # Exit button
        exit_button = QPushButton('Exit', self)
        exit_button.clicked.connect(self.close)
        self.setGeometry(300, 450, 150, 30)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


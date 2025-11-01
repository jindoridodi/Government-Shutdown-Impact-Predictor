
# dashboard.py

import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget, QPushButton, QLabel, QWebEngineView
from PyQt6.QtCore import Qt
from PyQt6.QtWebEngineWidgets import QWebEngineView
import pandas as pd
import folium
import plotly.express as px
import os

class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Government Shutdown Impact Dashboard')

        self.tab_widget = QTabWidget()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

        # Heatmap Tab
        heatmap_widget = QWidget()
        heatmap_layout = QVBoxLayout()
        heatmap_view = QWebEngineView()
        heatmap_label = QLabel("Folium Heatmap")
        heatmap_layout.addWidget(heatmap_label)
        heatmap_layout.addWidget(heatmap_view)
        heatmap_widget.setLayout(heatmap_layout)
        self.tab_widget.addTab(heatmap_widget, "Heatmap")

        # Top 10 Regions Tab
        top_10_widget = QWidget()
        top_10_layout = QVBoxLayout()
        top_10_chart = px.bar(data, x="region", y="risk_score", title="Top 10 Most Affected Regions",
                             labels={"risk_score": "Risk Score"}, height=300)
        top_10_chart_image = top_10_chart.to_image(format="png")
        top_10_image_label = QLabel()
        top_10_image_label.setPixmap(QtGui.QPixmap.fromImage(QtGui.QImage.fromData(top_10_chart_image.tobytes())))
        top_10_layout.addWidget(QLabel("Top 10 Regions by Risk Score"))
        top_10_layout.addWidget(top_10_image_label)
        top_10_widget.setLayout(top_10_layout)
        self.tab_widget.addTab(top_10_widget, "Top 10 Regions")

        # Summary Tab
        summary_widget = QWidget()
        summary_layout = QVBoxLayout()
        summary_label = QLabel("Summary Statistics")
        summary_layout.addWidget(summary_label)

        avg_risk_label = QLabel("Average Risk Score: ")
        avg_risk_value = QLabel(str(data['risk_score'].mean()))
        summary_layout.addWidget(avg_risk_label)
        summary_layout.addWidget(avg_risk_value)

        med_unemployment_label = QLabel("Median Unemployment Rate: ")
        med_unemployment_value = QLabel(str(data['unemployment_rate'].median()))
        summary_layout.addWidget(med_unemployment_label)
        summary_layout.addWidget(med_unemployment_value)

        most_vulnerable_label = QLabel("Most Vulnerable Region: ")
        most_vulnerable_value = QLabel(data.loc[data['risk_score'].idxmax(), 'region'])
        summary_layout.addWidget(most_vulnerable_label)
        summary_layout.addWidget(most_vulnerable_value)

        summary_widget.setLayout(summary_layout)
        self.tab_widget.addTab(summary_widget, "Summary")

        # Refresh Button
        refresh_button = QPushButton("Refresh Data")
        refresh_button.clicked.connect(self.refresh_data)
        self.layout.addWidget(refresh_button)

    def load_data(self):
        """
        Loads processed data from CSV and returns a pandas DataFrame.
        """
        data_path = './data/processed/regional_risk.csv'
        data = pd.read_csv(data_path)
        return data

    def create_heatmap(self, data):
        """
        Creates and displays a Folium heatmap.
        """
        m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)  # Center on roughly the middle of the U.S.
        folium.plugins.Heatmap(
            data[['lat', 'lon', 'risk_score']].values,
            radius=15,
            min_opacity=0.2,
            gradient={
                '0.25': 'blue',
                '0.5': 'green',
                '0.75': 'yellow',
                '1': 'red'
            }
        ).add_to(m)
        self.tab_widget.setCurrentIndex(0)  # Switch to Heatmap tab
        heatmap_view = self.tab_widget.widget(0).findChild(QWebEngineView)
        heatmap_view.setHtml(m.get_root().render())

    def create_top_10_chart(self, data):
        """
        Generates a Plotly bar chart of top 10 regions by risk score.
        """
        top_10 = data.nlargest(10, 'risk_score')
        top_10_chart = px.bar(top_10, x="region", y="risk_score", title="Top 10 Most Affected Regions",
                             labels={"risk_score": "Risk Score"}, height=300)
        top_10_chart_image = top_10_chart.to_image(format="png")
        return top_10_chart_image

    def refresh_data(self):
        """
        Refreshes data and updates visualizations.
        """
        data = self.load_data()
        self.create_heatmap(data)
        top_10_image = self.create_top_10_chart(data)
        # Save charts to visuals directory (implementation omitted for brevity)
        # self.save_charts(top_10_image)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = DashboardWidget()
    dashboard.show()
    sys.exit(app.exec())


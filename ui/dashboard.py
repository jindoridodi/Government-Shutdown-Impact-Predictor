
# dashboard.py
import sys
import os
import pandas as pd
import folium
import plotly.express as px

from PyQt6.QtWidgets import QApplication, QWidget, QTabWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtWebEngineWidgets import QWebEngineView  # correct import for the web view
from PyQt6.QtCore import Qt

from folium.plugins import HeatMap  # use HeatMap (correct class name)


class DashboardWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.data = None  # will hold the DataFrame
        self._setup_ui()
        self.refresh_data()  # load data and populate tabs

    def _setup_ui(self):
        self.setWindowTitle("Government Shutdown Impact Dashboard")

        self.tab_widget = QTabWidget()
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.tab_widget)
        self.setLayout(self.layout)

        # --- Heatmap Tab ---
        self.heatmap_widget = QWidget()
        heatmap_layout = QVBoxLayout(self.heatmap_widget)
        heatmap_layout.addWidget(QLabel("Folium Heatmap"))
        self.heatmap_view = QWebEngineView()
        heatmap_layout.addWidget(self.heatmap_view)
        self.tab_widget.addTab(self.heatmap_widget, "Heatmap")

        # --- Top 10 Regions Tab (render Plotly as HTML in web view; no QtGui/Kaleido needed) ---
        self.top10_widget = QWidget()
        top10_layout = QVBoxLayout(self.top10_widget)
        top10_layout.addWidget(QLabel("Top 10 Regions by Risk Score"))
        self.top10_view = QWebEngineView()
        top10_layout.addWidget(self.top10_view)
        self.tab_widget.addTab(self.top10_widget, "Top 10 Regions")

        # --- Summary Tab ---
        self.summary_widget = QWidget()
        summary_layout = QVBoxLayout(self.summary_widget)
        summary_layout.addWidget(QLabel("Summary Statistics"))

        self.avg_risk_label = QLabel("Average Risk Score: —")
        self.med_unemp_label = QLabel("Median Unemployment Rate: —")
        self.most_vulnerable_label = QLabel("Most Vulnerable Region: —")

        summary_layout.addWidget(self.avg_risk_label)
        summary_layout.addWidget(self.med_unemp_label)
        summary_layout.addWidget(self.most_vulnerable_label)

        self.tab_widget.addTab(self.summary_widget, "Summary")

        # --- Refresh Button ---
        refresh_button = QPushButton("Refresh Data")
        refresh_button.clicked.connect(self.refresh_data)
        self.layout.addWidget(refresh_button)

    # -------- Data / Rendering --------
    def load_data(self) -> pd.DataFrame:
        """Loads processed data from CSV and returns a pandas DataFrame."""
        data_path = "./data/processed/regional_risk.csv"
        df = pd.read_csv(data_path)

        # light validation
        required_cols = {"region", "risk_score"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        return df

    def create_heatmap(self, df: pd.DataFrame):
        """
        Creates and displays a Folium HeatMap.
        Expects point data columns 'lat' and 'lon'. If your data is polygons, use centroids.
        """
        if not {"lat", "lon"}.issubset(df.columns):
            # Fallback: if you only have polygons (not shown here),
            # compute representative points beforehand and add as 'lat'/'lon'.
            raise ValueError("Expected 'lat' and 'lon' columns for HeatMap.")

        m = folium.Map(location=[37.0902, -95.7129], zoom_start=4, tiles="cartodbpositron")
        HeatMap(
            df[["lat", "lon", "risk_score"]].values.tolist(),
            radius=15,
            min_opacity=0.2,
            max_opacity=0.95,
            blur=22,
        ).add_to(m)

        # Render in the web view
        self.heatmap_view.setHtml(m.get_root().render())

    def create_top_10_chart(self, df: pd.DataFrame):
        """Generates a Plotly bar chart of top 10 regions by risk score and shows it in a web view."""
        top_10 = df.nlargest(10, "risk_score")
        fig = px.bar(
            top_10,
            x="region",
            y="risk_score",
            title="Top 10 Most Affected Regions",
            labels={"risk_score": "Risk Score", "region": "Region"},
            height=360,
        )
        fig.update_layout(margin=dict(l=20, r=20, t=60, b=40))
        # Render as HTML (no Kaleido, no QtGui)
        self.top10_view.setHtml(fig.to_html(include_plotlyjs="cdn", full_html=False))

    def update_summary(self, df: pd.DataFrame):
        """Updates the summary labels."""
        avg_risk = df["risk_score"].mean()
        med_unemp = df["unemployment_rate"].median() if "unemployment_rate" in df.columns else float("nan")
        most_vulnerable = df.loc[df["risk_score"].idxmax(), "region"]

        self.avg_risk_label.setText(f"Average Risk Score: {avg_risk:.3f}")
        self.med_unemp_label.setText(
            "Median Unemployment Rate: " + ("—" if pd.isna(med_unemp) else f"{med_unemp:.3f}")
        )
        self.most_vulnerable_label.setText(f"Most Vulnerable Region: {most_vulnerable}")

    def refresh_data(self):
        """Refreshes data and updates visualizations."""
        self.data = self.load_data()
        self.create_heatmap(self.data)
        self.create_top_10_chart(self.data)
        self.update_summary(self.data)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = DashboardWidget()
    dashboard.show()
    sys.exit(app.exec())
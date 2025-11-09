import os
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
import pandas as pd
import folium
from folium import plugins
from utils.config import DATA_PATHS

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.vlayout = QVBoxLayout()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setSpacing(0)
        self.map_view = QWebEngineView()
        self.load_heatmap()
        self.vlayout.addWidget(self.map_view)
        self.setLayout(self.vlayout)

    def load_heatmap(self):
        # Load data from CSV and create heatmap using Folium
        base_dir = os.path.dirname(__file__)
        csv_path = os.path.join(DATA_PATHS.get('processed', os.path.join(os.path.dirname(__file__), 'data', 'processed')), "regional_risk.csv")
        
        try:
            data = pd.read_csv(csv_path)
            
            # Filter out rows with empty or NaN risk_score values
            # Convert risk_score to numeric, coercing errors to NaN
            data['risk_score'] = pd.to_numeric(data['risk_score'], errors='coerce')
            heatmap_data = data[['lat', 'lon', 'risk_score']].dropna()
            
            if len(heatmap_data) == 0:
                # No valid data - show empty map with message
                m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
                folium.Marker(
                    location=[37.0902, -95.7129],
                    popup="No risk score data available. Please run the predictor to generate risk scores using IBM Time Series Forecasting.",
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
            else:
                # Create map centered on US
                m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
                
                # Prepare heatmap data: [lat, lon, weight] format
                heatmap_values = heatmap_data[['lat', 'lon', 'risk_score']].values.tolist()
                
                # Add heatmap layer
                plugins.HeatMap(
                    heatmap_values,
                    radius=15,
                    min_opacity=0.2,
                    max_zoom=18,
                    gradient={
                        0.2: 'blue',
                        0.4: 'cyan',
                        0.6: 'lime',
                        0.8: 'yellow',
                        1.0: 'red'
                    }
                ).add_to(m)
            
            self.map_view.setHtml(m.get_root().render())
        except Exception as e:
            # Error loading data - show error message
            m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)
            folium.Marker(
                location=[37.0902, -95.7129],
                popup=f"Error loading heatmap data: {str(e)}",
                icon=folium.Icon(color='red', icon='warning-sign')
            ).add_to(m)
            self.map_view.setHtml(m.get_root().render())

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle('Predictive Risk Dashboard')
        self.setGeometry(100, 100, 800, 600)

        # Create dashboard widget that fills the entire window
        self.dashboard = Dashboard()
        self.setCentralWidget(self.dashboard)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.showMaximized()  # Start the window maximized
    sys.exit(app.exec())


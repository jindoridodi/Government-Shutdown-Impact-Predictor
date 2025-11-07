
# visualization.py

import pandas as pd
import folium
import plotly.express as px
import geopandas as gpd
import os

def create_heatmap(data_path, output_html):
    """
    Generates an interactive Folium heatmap of the U.S. risk scores.
    """
    # Load data
    data = pd.read_csv(data_path)

    # Assuming 'geometry' column contains GeoJSON for region boundaries
    gdf = gpd.GeoDataFrame.from_features(data[['geometry', 'risk_score']].to_dict('records'))

    # Create Folium map centered on the U.S.
    m = folium.Map(location=[37.0902, -95.7129], zoom_start=4)  # Center on roughly the middle of the U.S.

    # Add heatmap layer
    folium.plugins.Heatmap(
        gdf.geometry.apply(lambda x: [(x.bounds[1], x.bounds[0], x.bounds[3], x.bounds[2], data['risk_score'][i])]).tolist(),
        radius=15,
        min_opacity=0.2,
        gradient={
            '0.25': 'blue',
            '0.5': 'green',
            '0.75': 'yellow',
            '1': 'red'
        }
    ).add_to(m)

    # Add tooltip with risk score on hover
    for i, row in gdf.iterrows():
        folium.Marker(
            location=(row['geometry'].centroid.y, row['geometry'].centroid.x),
            popup=f"Risk Score: {row['risk_score']}",
            icon=folium.Icon(color='red', icon='info-sign')
        ).add_to(m)

    # Save map as HTML
    m.save(output_html)

def create_trend_chart(data_path, output_html):
    """
    Creates a Plotly line chart of predicted risk trends over time.
    """
    data = pd.read_csv(data_path)

    # Assuming 'date' column exists for time series
    fig = px.line(data, x='date', y='predicted_risk', title='Predicted Risk Trends')
    fig.update_layout(
        xaxis_title='Date',
        yaxis_title='Predicted Risk Score'
    )
    fig.write_html(output_html)

if __name__ == "__main__":
    # Define output paths
    heatmap_output = os.path.join('/data/visuals', 'regional_risk_heatmap.html')
    trend_output = os.path.join('/data/visuals', 'risk_trends.html')

    # Create visualizations
    create_heatmap('/data/processed/regional_risk.csv', heatmap_output)
    create_trend_chart('/data/processed/regional_risk.csv', trend_output)


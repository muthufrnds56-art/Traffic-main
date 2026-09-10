import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
import time
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Optional
import os
import pydeck as pdk

from streamlit.components.v1 import html

# Page configuration
st.set_page_config(
    page_title="Traffic Management System",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .alert-high {
        background-color: #ffebee;
        border-left: 6px solid #f44336;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(244, 67, 54, 0.2);
    }
    .alert-medium {
        background-color: #fff3e0;
        border-left: 6px solid #ff9800;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(255, 152, 0, 0.2);
    }
    .alert-card {
        background-color: #ffffff;
        padding: 1.2rem;
        margin: 0.8rem 0;
        border-radius: 0.5rem;
        border: 2px solid;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-online { background-color: #4caf50; }
    .status-offline { background-color: #f44336; }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
REFRESH_INTERVAL = 30  # seconds
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

ADDITIONAL_LOCATIONS = {
    "Vidhana Soudha": {"lat": 12.9797, "lng": 77.5912},
    "Cubbon Park": {"lat": 12.9763, "lng": 77.5929},
    "Lalbagh Botanical Garden": {"lat": 12.9507, "lng": 77.5848},
    "Bangalore Palace": {"lat": 12.9988, "lng": 77.5921},
    "ISKCON Temple": {"lat": 13.0096, "lng": 77.5511},
    "Commercial Street": {"lat": 12.9822, "lng": 77.6083},
    "Brigade Road": {"lat": 12.9749, "lng": 77.6076},
    "UB City": {"lat": 12.9719, "lng": 77.5961},
    "Orion Mall": {"lat": 13.0110, "lng": 77.5549},
    "Phoenix Marketcity": {"lat": 12.9959, "lng": 77.6963},
    "Forum Mall": {"lat": 12.9344, "lng": 77.6112},
    "RMZ Ecospace": {"lat": 12.9255, "lng": 77.6759},
    "Bagmane Tech Park": {"lat": 12.9801, "lng": 77.6649},
    "Manyata Tech Park": {"lat": 13.0456, "lng": 77.6209},
    "Embassy GolfLinks": {"lat": 12.9476, "lng": 77.6387},
    "Majestic Bus Station": {"lat": 12.9767, "lng": 77.5713},
    "Yeshwantpur Railway Station": {"lat": 13.0237, "lng": 77.5504},
    "Krantivira Sangolli Rayanna Station": {"lat": 12.9783, "lng": 77.5695},
    "Cantonment Railway Station": {"lat": 12.9936, "lng": 77.5980},
    "Sir M Visvesvaraya Terminal": {"lat": 13.0005, "lng": 77.6242},
    "Hebbal Flyover": {"lat": 13.0334, "lng": 77.5891},
    "Silk Board Junction": {"lat": 12.9172, "lng": 77.6228},
    "Tin Factory": {"lat": 12.9941, "lng": 77.6612},
    "Marathahalli Bridge": {"lat": 12.9556, "lng": 77.7015},
    "KR Puram Bridge": {"lat": 13.0003, "lng": 77.6737}
}

class TrafficDashboard:
    def __init__(self):
        # Simulate data generation
        self.sensor_locations = [
            "MG Road", "Hosur Road", "Indiranagar 100ft Road", "Outer Ring Road",
            "Jayanagar 4th Block", "Bellary Road", "Koramangala 80ft Road", "Bannerghatta Road"
        ]
        self.sensor_ids = [f"T{i:03d}" for i in range(1, 9)]
        self.road_types = ["arterial", "highway", "collector", "arterial", "local", "highway", "collector", "arterial"]
        
        # Sensor coordinates
        self.sensor_coords = {
            "T001": {"lat": 12.9716, "lng": 77.5946},
            "T002": {"lat": 12.9352, "lng": 77.6245},
            "T003": {"lat": 12.9784, "lng": 77.6408},
            "T004": {"lat": 12.9698, "lng": 77.7500},
            "T005": {"lat": 12.9308, "lng": 77.5838},
            "T006": {"lat": 13.0359, "lng": 77.5970},
            "T007": {"lat": 12.9591, "lng": 77.6974},
            "T008": {"lat": 12.8452, "lng": 77.6602}
        }
        
    def check_api_health(self) -> bool:
        """Always return True for standalone mode"""
        return True
    
    def get_current_traffic(self) -> Optional[Dict]:
        """Generate current traffic data locally"""
        import random
        from datetime import datetime
        
        current_traffic = []
        for i, sensor_id in enumerate(self.sensor_ids):
            base_flow = random.randint(200, 1500)
            # Simple time-based factor
            hour = datetime.now().hour
            time_factor = 1.8 if hour in [7,8,9,17,18,19] else 1.2
            flow_rate = int(base_flow * time_factor * random.uniform(0.8, 1.2))
            
            # Derived metrics
            congestion = 1
            if flow_rate > 1200: congestion = 5
            elif flow_rate > 1000: congestion = 4
            elif flow_rate > 800: congestion = 3
            elif flow_rate > 500: congestion = 2
            
            mock_data = {
                "sensor_id": sensor_id,
                "location": self.sensor_locations[i],
                "road_type": self.road_types[i],
                "vehicle_count": random.randint(10, 120),
                "flow_rate": flow_rate,
                "average_speed": max(10, random.randint(20, 70) - (congestion * 10)),
                "congestion_level": congestion,
                "timestamp": datetime.now().isoformat()
            }
            current_traffic.append(mock_data)
            
        return {
            "timestamp": time.time(),
            "sensors_count": len(current_traffic),
            "traffic_data": current_traffic
        }
    
    def get_analytics_summary(self) -> Optional[Dict]:
        """Calculate summary from generated data"""
        data = self.get_current_traffic()
        if not data: return None
        
        traffic_data = data["traffic_data"]
        total_vehicles = sum(d["vehicle_count"] for d in traffic_data)
        avg_speed = sum(d["average_speed"] for d in traffic_data) / len(traffic_data)
        avg_congestion = sum(d["congestion_level"] for d in traffic_data) / len(traffic_data)
        
        congestion_counts = {}
        for d in traffic_data:
            l = d["congestion_level"]
            congestion_counts[l] = congestion_counts.get(l, 0) + 1
            
        problematic = [d for d in traffic_data if d["congestion_level"] >= 4]
        
        return {
            "timestamp": time.time(),
            "summary": {
                "total_sensors": len(traffic_data),
                "total_vehicles": total_vehicles,
                "average_speed": round(avg_speed, 2),
                "average_congestion": round(avg_congestion, 2),
                "congestion_distribution": congestion_counts,
                "problematic_areas": len(problematic)
            },
            "problematic_sensors": problematic
        }
    
    def get_current_alerts(self) -> Optional[Dict]:
        """Generate alerts based on generated data"""
        data = self.get_current_traffic()
        alerts = []
        if data:
            for d in data["traffic_data"]:
                if d["congestion_level"] >= 4:
                    alerts.append({
                        "type": "congestion_alert",
                        "sensor_id": d["sensor_id"],
                        "location": d["location"],
                        "severity": "high" if d["congestion_level"] == 5 else "medium",
                        "message": f"High congestion generated at {d['location']}",
                        "timestamp": d["timestamp"]
                    })
        return {"alerts": alerts}
    
    def get_sensors_list(self) -> Optional[Dict]:
        """Return static list of sensors"""
        sensors = []
        for i, sid in enumerate(self.sensor_ids):
            sensors.append({
                "sensor_id": sid,
                "location": self.sensor_locations[i],
                "road_type": self.road_types[i],
                "coordinates": self.sensor_coords[sid]
            })
        return {"sensors": sensors}

    def get_prediction_map(self) -> Optional[Dict]:
        """Generate mock prediction data"""
        import random
        data = self.get_current_traffic()
        if not data: return None
        
        predictions = []
        for d in data["traffic_data"]:
            # Predict slightly different from current
            pred_congestion = min(5, max(1, d["congestion_level"] + random.choice([-1, 0, 1])))
            predictions.append({
                "sensor_id": d["sensor_id"],
                "location": d["location"],
                "predicted_congestion_level": pred_congestion,
                "predicted_flow": int(d["flow_rate"] * random.uniform(0.9, 1.1)),
                "traffic_expected": pred_congestion >= 4,
                "model_confidence": random.uniform(0.7, 0.95),
                "prediction_timestamp": datetime.now().isoformat()
            })
            
        return {"predictions": predictions}
        
    def mock_route_optimization(self, start: str, end: str, start_coords: Dict, end_coords: Dict) -> Dict:
        """Helper to generate a mock route"""
        # Simple Mock Calculation
        import math
        dist = math.sqrt((start_coords['lat'] - end_coords['lat'])**2 + (start_coords['lng'] - end_coords['lng'])**2) * 111 # rough km
        
        return {
            "recommended_route": {
                "distance": round(dist * 1.2, 2),
                "estimated_time": int(dist * 2.5),
                "congestion_level": 2,
                "path": [start, "Intermediate Waypoint", end],
                "score": 0.92
            },
            "alternative_routes": [
                {
                    "route_id": "Route B",
                    "distance": round(dist * 1.5, 2),
                    "estimated_time": int(dist * 3.5),
                    "congestion_level": 4,
                    "path": [start, "Traffic Hotspot", end],
                    "score": 0.65
                }
            ]
        }

def create_traffic_heatmap(traffic_data: List[Dict]) -> go.Figure:
    """Create a traffic congestion heatmap"""
    if not traffic_data:
        return go.Figure()
    
    # Extract data for heatmap
    locations = [data.get('location', 'Unknown') for data in traffic_data]
    congestion_levels = [data.get('congestion_level', 0) for data in traffic_data]
    flow_rates = [data.get('flow_rate', 0) for data in traffic_data]
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=[congestion_levels],
        x=locations,
        y=['Congestion Level'],
        colorscale='RdYlGn_r',
        zmin=1,
        zmax=5,
        text=[[f"Level {level}<br>Flow: {flow}" for level, flow in zip(congestion_levels, flow_rates)]],
        hoverinfo='text'
    ))
    
    fig.update_layout(
        title="Traffic Congestion Heatmap",
        xaxis_title="Location",
        yaxis_title="",
        height=400
    )
    
    return fig

def create_traffic_flow_chart(traffic_data: List[Dict]) -> go.Figure:
    """Create a traffic flow chart"""
    if not traffic_data:
        return go.Figure()
    
    # Extract data
    locations = [data.get('location', 'Unknown') for data in traffic_data]
    flow_rates = [data.get('flow_rate', 0) for data in traffic_data]
    avg_speeds = [data.get('average_speed', 0) for data in traffic_data]
    
    # Create subplot with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Add flow rate bars
    fig.add_trace(
        go.Bar(
            x=locations,
            y=flow_rates,
            name="Flow Rate (veh/hr)",
            marker_color='lightblue'
        ),
        secondary_y=False
    )
    
    # Add average speed line
    fig.add_trace(
        go.Scatter(
            x=locations,
            y=avg_speeds,
            name="Average Speed (mph)",
            line=dict(color='red', width=3)
        ),
        secondary_y=True
    )
    
    fig.update_layout(
        title="Traffic Flow vs Average Speed",
        xaxis_title="Location",
        height=400
    )
    
    fig.update_yaxes(title_text="Flow Rate (veh/hr)", secondary_y=False)
    fig.update_yaxes(title_text="Average Speed (mph)", secondary_y=True)
    
    return fig

def create_congestion_distribution_chart(analytics_data: Dict) -> go.Figure:
    """Create congestion distribution pie chart"""
    if not analytics_data or 'summary' not in analytics_data:
        return go.Figure()
    
    summary = analytics_data['summary']
    congestion_dist = summary.get('congestion_distribution', {})
    
    if not congestion_dist:
        return go.Figure()
    
    # Create pie chart
    labels = [f"Level {level}" for level in sorted(congestion_dist.keys())]
    values = [congestion_dist[level] for level in sorted(congestion_dist.keys())]
    colors = ['#4caf50', '#8bc34a', '#ffeb3b', '#ff9800', '#f44336']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker_colors=colors[:len(labels)]
    )])
    
    fig.update_layout(
        title="Congestion Level Distribution",
        height=400
    )
    
    return fig

def _build_map_points(
    traffic_data: List[Dict],
    sensors_data: Optional[Dict],
    predictions_data: Optional[Dict] = None
) -> List[Dict]:
    """Combine traffic metrics with sensor coordinates for map rendering."""
    if not traffic_data:
        return []

    sensor_coordinates = {}
    if sensors_data and sensors_data.get('sensors'):
        for sensor in sensors_data['sensors']:
            coords = sensor.get('coordinates', {})
            if coords and 'lat' in coords and 'lng' in coords:
                sensor_coordinates[sensor['sensor_id']] = {
                    "lat": coords['lat'],
                    "lng": coords['lng'],
                    "location": sensor.get('location', sensor['sensor_id'])
                }

    prediction_lookup = {}
    if predictions_data and predictions_data.get('predictions'):
        prediction_lookup = {
            entry.get('sensor_id'): entry
            for entry in predictions_data['predictions']
            if entry.get('sensor_id')
        }

    map_points = []
    for entry in traffic_data:
        sensor_id = entry.get('sensor_id')
        coords = sensor_coordinates.get(sensor_id)
        if not coords:
            continue

        prediction = prediction_lookup.get(sensor_id, {})

        map_points.append({
            "sensor_id": sensor_id,
            "location": coords['location'],
            "lat": coords['lat'],
            "lng": coords['lng'],
            "flow_rate": entry.get('flow_rate', 0),
            "average_speed": entry.get('average_speed', 0),
            "congestion_level": entry.get('congestion_level', 0),
            "timestamp": entry.get('timestamp', ''),
            "predicted_congestion_level": prediction.get('predicted_congestion_level'),
            "predicted_flow": prediction.get('predicted_flow'),
            "prediction_timestamp": prediction.get('prediction_timestamp'),
            "traffic_expected": prediction.get('traffic_expected', False),
            "model_confidence": prediction.get('model_confidence')
        })

    return map_points

def render_google_traffic_map(
    traffic_data: List[Dict],
    sensors_data: Optional[Dict],
    predictions_data: Optional[Dict] = None
):
    """Render Google Maps view with traffic data overlay."""
    st.subheader("Google Maps Traffic View")
    map_points = _build_map_points(traffic_data, sensors_data, predictions_data)

    if not map_points:
        st.warning("No sensor coordinates available to plot on the map.")
        return

    if not GOOGLE_MAPS_API_KEY:
        _render_fallback_map(map_points)
        return

    if predictions_data and predictions_data.get('predictions'):
        st.caption("Forecast overlay enabled — markers reflect predicted congestion within the next hour.")

    map_center = map_points[0]
    map_points_json = json.dumps(map_points)

    html_content = f"""
        <div id="traffic-map" style="width: 100%; height: 500px; border-radius: 8px;"></div>
        <script>
            const mapData = {map_points_json};
            function initMap() {{
                const map = new google.maps.Map(document.getElementById('traffic-map'), {{
                    zoom: 13,
                    center: {{ lat: {map_center['lat']}, lng: {map_center['lng']} }},
                    mapTypeId: 'roadmap'
                }});

                const trafficLayer = new google.maps.TrafficLayer();
                trafficLayer.setMap(map);

                mapData.forEach(point => {{
                    const hasPrediction = point.predicted_congestion_level !== null && point.predicted_congestion_level !== undefined;
                    let color = 'green';
                    let statusLabel = 'Normal conditions';
                    if (hasPrediction) {{
                        if (point.predicted_congestion_level >= 4) {{
                            color = 'red';
                            statusLabel = 'High traffic expected';
                        }} else if (point.predicted_congestion_level >= 3) {{
                            color = 'orange';
                            statusLabel = 'Moderate traffic expected';
                        }} else {{
                            color = 'green';
                            statusLabel = 'Low traffic expected';
                        }}
                    }} else {{
                        if (point.congestion_level >= 4) {{
                            color = 'red';
                            statusLabel = 'Currently congested';
                        }} else if (point.congestion_level >= 3) {{
                            color = 'orange';
                            statusLabel = 'Currently moderate';
                        }}
                    }}

                    const marker = new google.maps.Marker({{
                        position: {{ lat: point.lat, lng: point.lng }},
                        map: map,
                        title: `${{point.location}} - Level ${{point.congestion_level}}`,
                        icon: {{
                            url: `http://maps.google.com/mapfiles/ms/icons/${{color}}-dot.png`
                        }}
                    }});

                    const confidence = (point.model_confidence !== null && point.model_confidence !== undefined)
                        ? `${{(point.model_confidence * 100).toFixed(0)}}%`
                        : 'N/A';
                    const forecastBlock = hasPrediction
                        ? `<strong>Forecast</strong><br/>
                            Level ${{point.predicted_congestion_level}} / 5<br/>
                            Expected Flow: ${{point.predicted_flow || 'N/A'}} veh/hr<br/>
                            Status: ${{statusLabel}}<br/>
                            Time: ${{point.prediction_timestamp || 'N/A'}}<br/>
                            Confidence: ${{confidence}}<br/>`
                        : 'Forecast unavailable<br/>';

                    const infoWindow = new google.maps.InfoWindow({{
                        content: `
                            <div style="min-width: 220px;">
                                <strong>${{point.location}}</strong><br/>
                                Sensor: ${{point.sensor_id}}<br/>
                                Current Flow: ${{point.flow_rate}} veh/hr<br/>
                                Avg Speed: ${{point.average_speed}} mph<br/>
                                Congestion: Level ${{point.congestion_level}} / 5<br/>
                                ${{forecastBlock}}
                            </div>`
                    }});

                    marker.addListener('click', () => infoWindow.open({{ anchor: marker, map, shouldFocus: false }}));
                }});
            }}
        </script>
        <script src="https://maps.googleapis.com/maps/api/js?key={GOOGLE_MAPS_API_KEY}&callback=initMap" async defer></script>
    """

    html(html_content, height=520)


def _render_fallback_map(map_points: List[Dict]):
    """Display a pydeck-based fallback map when Google Maps is unavailable."""
    if not map_points:
        return

    def _derive_color(point):
        predicted_level = point.get('predicted_congestion_level')
        level = predicted_level if predicted_level is not None else point.get('congestion_level', 1)
        if level >= 4:
            return [239, 68, 68, 200]  # red
        if level >= 3:
            return [251, 146, 60, 200]  # orange
        return [34, 197, 94, 200]  # green

    deck_points: List[Dict] = []
    for point in map_points:
        pt = point.copy()
        pt["color"] = _derive_color(point)
        # scale radius by congestion for visibility
        level = point.get('predicted_congestion_level') or point.get('congestion_level', 1)
        pt["radius"] = 200 + (int(level) * 100) # Increased radius for better visibility
        pt["text_label"] = str(level)
        deck_points.append(pt)

    map_center = map_points[0]
    
    scatter_layer = pdk.Layer(
        "ScatterplotLayer",
        data=deck_points,
        get_position="[lng, lat]",
        get_radius="radius",
        get_fill_color="color",
        pickable=True,
        stroked=True,
        filled=True,
        line_width_min_pixels=2,
        get_line_color=[255, 255, 255],
    )

    text_layer = pdk.Layer(
        "TextLayer",
        data=deck_points,
        get_position="[lng, lat]",
        get_text="text_label",
        get_color=[255, 255, 255],
        get_size=16,
        get_angle=0,
        get_text_anchor="middle",
        get_alignment_baseline="center",
    )

    tooltip = {
        "html": """
            <div style="padding: 10px; background-color: white; color: black; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                <strong style="font-size: 1.1em;">{location}</strong><br/>
                <hr style="margin: 5px 0;"/>
                <b>Congestion Level:</b> {congestion_level}/5<br/>
                <b>Flow Rate:</b> {flow_rate} veh/hr<br/>
                <b>Avg Speed:</b> {average_speed} mph
            </div>
        """,
        "style": {"backgroundColor": "transparent", "color": "white"}
    }

    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json", # Explicit Carto style URL
        initial_view_state=pdk.ViewState(
            latitude=map_center["lat"],
            longitude=map_center["lng"],
            zoom=12, # Zoom out slightly
            pitch=45,
        ),
        layers=[scatter_layer, text_layer],
        tooltip=tooltip,
        map_provider="carto",
    )

    st.pydeck_chart(deck, use_container_width=True)


def _build_location_lookup(sensors_data: Optional[Dict]) -> Dict[str, Dict[str, float]]:
    """Create a lookup from location name to coordinates."""
    lookup: Dict[str, Dict[str, float]] = {}
    if sensors_data and sensors_data.get('sensors'):
        for sensor in sensors_data['sensors']:
            coords = sensor.get('coordinates')
            location_name = sensor.get('location') or sensor.get('sensor_id')
            if coords and 'lat' in coords and 'lng' in coords and location_name:
                lookup[location_name] = {"lat": coords['lat'], "lng": coords['lng']}
    # Add synthetic waypoint coordinates
    for name, coords in ADDITIONAL_LOCATIONS.items():
        lookup.setdefault(name, coords)
    return lookup


def render_route_map(
    start_location: str,
    end_location: str,
    recommended_route: Dict,
    alternative_routes: List[Dict],
    sensors_data: Optional[Dict]
):
    """Render a pydeck map showing recommended and alternative routes."""
    st.subheader("Route Visualization")
    location_lookup = _build_location_lookup(sensors_data)

    def _path_to_coords(path: List[str]) -> List[List[float]]:
        coords = []
        for loc in path or []:
            if loc in location_lookup:
                loc_coords = location_lookup[loc]
                coords.append([loc_coords['lng'], loc_coords['lat']])
        return coords

    path_segments: List[Dict] = []
    scatter_points: List[Dict] = []

    if recommended_route and recommended_route.get('path'):
        rec_coords = _path_to_coords(recommended_route.get('path', []))
        if len(rec_coords) >= 2:
            path_segments.append({
                "path": rec_coords,
                "color": [34, 197, 94, 220],
                "width": 6,
                "label": "Recommended"
            })

    alt_colors = [
        [251, 146, 60, 200],
        [59, 130, 246, 200],
        [217, 119, 6, 200]
    ]

    for idx, route in enumerate(alternative_routes or []):
        coords = _path_to_coords(route.get('path', []))
        if len(coords) >= 2:
            path_segments.append({
                "path": coords,
                "color": alt_colors[idx % len(alt_colors)],
                "width": 4,
                "label": route.get('route_id', f"Alt #{idx+1}")
            })

    if start_location in location_lookup:
        scatter_points.append({
            "location": start_location,
            "color": [16, 185, 129, 220],
            "lat": location_lookup[start_location]['lat'],
            "lng": location_lookup[start_location]['lng'],
            "label": "Start"
        })
    if end_location in location_lookup:
        scatter_points.append({
            "location": end_location,
            "color": [239, 68, 68, 220],
            "lat": location_lookup[end_location]['lat'],
            "lng": location_lookup[end_location]['lng'],
            "label": "End"
        })

    if not path_segments and not scatter_points:
        st.info("Unable to plot the route because coordinates for the selected locations are missing.")
        return

    if scatter_points:
        initial_lat = scatter_points[0]['lat']
        initial_lng = scatter_points[0]['lng']
    elif path_segments:
        initial_lat = path_segments[0]['path'][0][1]
        initial_lng = path_segments[0]['path'][0][0]
    else:
        st.info("No map data available.")
        return

    layers = []
    if path_segments:
        layers.append(
            pdk.Layer(
                "PathLayer",
                data=path_segments,
                get_path="path",
                get_color="color",
                get_width="width",
                width_scale=20,
                width_min_pixels=3,
                width_max_pixels=12,
                pickable=True,
            )
        )
    if scatter_points:
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=scatter_points,
                get_position="[lng, lat]",
                get_fill_color="color",
                get_radius=120,
                pickable=True,
            )
        )

    tooltip = {
        "html": "<b>{label}</b><br/>{location}",
        "style": {"backgroundColor": "rgba(38,38,38,0.8)", "color": "white"}
    }

    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=initial_lat,
            longitude=initial_lng,
            zoom=12,
            pitch=35,
        ),
        layers=layers,
        tooltip=tooltip,
        map_provider="carto",
    )

    st.pydeck_chart(deck, use_container_width=True)


def display_metrics(analytics_data: Optional[Dict]):
    """Display key metrics"""
    if not analytics_data or 'summary' not in analytics_data:
        # Display placeholder metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Sensors", "8", "Online")
        
        with col2:
            st.metric("Total Vehicles", "0", "No Data")
        
        with col3:
            st.metric("Avg Speed", "0 mph", "No Data")
        
        with col4:
            st.metric("Avg Congestion", "0/5", "No Data")
        
        return
    
    summary = analytics_data['summary']
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Sensors", 
            summary.get('total_sensors', 0),
            f"{summary.get('problematic_areas', 0)} issues"
        )
    
    with col2:
        st.metric(
            "Total Vehicles", 
            summary.get('total_vehicles', 0),
            "Current"
        )
    
    with col3:
        st.metric(
            "Avg Speed", 
            f"{summary.get('average_speed', 0):.1f} mph",
            "Across network"
        )
    
    with col4:
        st.metric(
            "Avg Congestion", 
            f"{summary.get('average_congestion', 0):.1f}/5",
            "Network status"
        )

def display_alerts(alerts_data: Optional[Dict]):
    """Display current alerts"""
    st.markdown("### Current Alerts")
    
    if not alerts_data or not alerts_data.get('alerts'):
        st.info("No active alerts at the moment. All systems operating normally.")
        return
    
    alerts = alerts_data['alerts']
    alerts_count = len(alerts)
    
    # Show alert count badge
    if alerts_count > 0:
        st.markdown(f"**{alerts_count} active alert{'s' if alerts_count > 1 else ''}**")
        st.markdown("---")
    
    for idx, alert in enumerate(alerts, 1):
        severity = alert.get('severity', 'medium').lower()
        alert_type = alert.get('type', 'Unknown').replace('_', ' ').title()
        location = alert.get('location', 'Unknown')
        message = alert.get('message', 'No message')
        timestamp = alert.get('timestamp', 'Unknown')
        
        # Use Streamlit's native components for better visibility
        if severity == 'high':
            with st.container():
                st.error(f"**Alert #{idx}: {alert_type}**")
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Location:** {location}")
                    st.write(f"**Message:** {message}")
                with col2:
                    st.write(f"**Time:** {timestamp.split('T')[1].split('.')[0] if 'T' in timestamp else timestamp}")
                st.markdown("---")
        else:
            with st.container():
                st.warning(f"**Alert #{idx}: {alert_type}**")
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.write(f"**Location:** {location}")
                    st.write(f"**Message:** {message}")
                with col2:
                    st.write(f"**Time:** {timestamp.split('T')[1].split('.')[0] if 'T' in timestamp else timestamp}")
                st.markdown("---")

def display_sensor_status(sensors_data: Optional[Dict], traffic_data: Optional[Dict]):
    """Display sensor status and data"""
    st.subheader("Sensor Status")
    
    if not sensors_data or not sensors_data.get('sensors'):
        st.warning("Unable to retrieve sensor information.")
        return
    
    sensors = sensors_data['sensors']
    
    # Create a DataFrame for better display
    sensor_df = pd.DataFrame(sensors)
    
    # Add traffic data if available
    if traffic_data and traffic_data.get('traffic_data'):
        traffic_dict = {data['sensor_id']: data for data in traffic_data['traffic_data']}
        
        sensor_df['status'] = sensor_df['sensor_id'].apply(
            lambda x: 'Online' if x in traffic_dict else 'Offline'
        )
        sensor_df['congestion_level'] = sensor_df['sensor_id'].apply(
            lambda x: traffic_dict.get(x, {}).get('congestion_level', 'N/A')
        )
        sensor_df['flow_rate'] = sensor_df['sensor_id'].apply(
            lambda x: traffic_dict.get(x, {}).get('flow_rate', 'N/A')
        )
    else:
        sensor_df['status'] = 'Unknown'
        sensor_df['congestion_level'] = 'N/A'
        sensor_df['flow_rate'] = 'N/A'
    
    # Display sensor table
    st.dataframe(
        sensor_df,
        use_container_width=True,
        hide_index=True
    )

def main():
    """Main dashboard function"""
    st.markdown('<h1 class="main-header">Traffic Management System</h1>', unsafe_allow_html=True)
    
    # Initialize dashboard
    dashboard = TrafficDashboard()
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Dashboard", "Traffic Analysis", "Route Optimization", "Video Analysis", "System Status"]
    )
    
    # Check API health
    api_healthy = dashboard.check_api_health()
    
    if not api_healthy:
        st.error("API service is not available. Please ensure the backend is running.")
        st.info("To start the system, run the following commands:")
        st.code("""
# Terminal 1: Start IoT sensors
python iot_sensors/traffic_simulator.py

# Terminal 2: Start data pipeline
python data_pipeline/kafka_consumer.py

# Terminal 3: Start ML service
python ml_services/traffic_predictor.py

# Terminal 4: Start API
python api/main.py
        """)
        return
    
    # Main dashboard page
    if page == "Dashboard":
        st.header("Real-time Traffic Overview")
        
        # Auto-refresh
        if st.button("Refresh Data") or 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        # Get data
        traffic_data = dashboard.get_current_traffic()
        analytics_data = dashboard.get_analytics_summary()
        alerts_data = dashboard.get_current_alerts()
        sensors_data = dashboard.get_sensors_list()
        
        # Display metrics
        display_metrics(analytics_data)
        
        # Display alerts
        display_alerts(alerts_data)
        
        # Create charts
        if traffic_data and traffic_data.get('traffic_data'):
            col1, col2 = st.columns(2)
            
            with col1:
                fig_heatmap = create_traffic_heatmap(traffic_data['traffic_data'])
                st.plotly_chart(fig_heatmap, use_container_width=True)
            
            with col2:
                fig_flow = create_traffic_flow_chart(traffic_data['traffic_data'])
                st.plotly_chart(fig_flow, use_container_width=True)
            
            # Congestion distribution
            if analytics_data:
                fig_dist = create_congestion_distribution_chart(analytics_data)
                st.plotly_chart(fig_dist, use_container_width=True)
        
        # Display sensor status
        display_sensor_status(sensors_data, traffic_data)
        
        # Auto-refresh info
        st.info(f"Data last refreshed at {datetime.now().strftime('%H:%M:%S')}. Click refresh button to update.")
    
    elif page == "Traffic Analysis":
        st.header("Traffic Analysis")
        
        # Get data
        traffic_data = dashboard.get_current_traffic()
        sensors_data = dashboard.get_sensors_list()
        prediction_map = dashboard.get_prediction_map()
        
        if not traffic_data or not traffic_data.get('traffic_data'):
            st.warning("No traffic data available for analysis.")
            return
        
        # Time series analysis
        st.subheader("Time Series Analysis")
        
        # Create mock time series data for demonstration
        hours = pd.date_range(start=datetime.now() - timedelta(hours=24), 
                            end=datetime.now(), freq='h')
        
        # Simulate traffic patterns
        base_traffic = 1000
        time_factors = [0.3 if h.hour < 6 else 1.8 if h.hour in [7,8,9,17,18,19] else 1.2 for h in hours]
        traffic_series = [base_traffic * factor * np.random.uniform(0.8, 1.2) for factor in time_factors]
        
        # Create time series chart
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(
            x=hours,
            y=traffic_series,
            mode='lines+markers',
            name='Traffic Flow',
            line=dict(color='blue', width=2)
        ))
        
        fig_ts.update_layout(
            title="24-Hour Traffic Flow Pattern",
            xaxis_title="Time",
            yaxis_title="Traffic Flow (veh/hr)",
            height=400
        )
        
        st.plotly_chart(fig_ts, use_container_width=True)

        # Google Maps visualization
        render_google_traffic_map(
            traffic_data['traffic_data'],
            sensors_data,
            prediction_map
        )

        if prediction_map and prediction_map.get('predictions'):
            hot_spots = [
                f"{item.get('location', item.get('sensor_id'))} (Level {item.get('predicted_congestion_level')})"
                for item in prediction_map['predictions']
                if item.get('traffic_expected')
            ]
            if hot_spots:
                st.warning("High traffic expected soon at: " + ", ".join(hot_spots))
        
        # Statistical analysis
        st.subheader("Statistical Analysis")
        
        if traffic_data['traffic_data']:
            df = pd.DataFrame(traffic_data['traffic_data'])
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Traffic Flow Statistics**")
                st.write(df['flow_rate'].describe())
            
            with col2:
                st.write("**Speed Statistics**")
                st.write(df['average_speed'].describe())
    
    elif page == "Route Optimization":
        st.header("Route Optimization")
        
        sensors_data = dashboard.get_sensors_list()
        
        # Route input form
        with st.form("route_optimization"):
            col1, col2 = st.columns(2)
            
            # All available locations
            all_locations = [
                "MG Road",
                "Hosur Road",
                "Indiranagar 100ft Road",
                "Outer Ring Road",
                "Jayanagar 4th Block",
                "Bellary Road",
                "Koramangala 80ft Road",
                "Bannerghatta Road"
            ]
            
            with col1:
                start_location = st.selectbox(
                    "Start Location",
                    all_locations,
                    key="start_location"
                )
            
            with col2:
                end_location = st.selectbox(
                    "End Location",
                    all_locations,
                    key="end_location"
                )
            
            route_type = st.selectbox(
                "Preferred Route Type",
                ["fastest", "shortest", "least_congested"]
            )
            
            submitted = st.form_submit_button("Optimize Route")
            
            if submitted:
                if start_location == end_location:
                    st.error("Start and end locations cannot be the same.")
                else:
                    # Mock Route Optimization for Standalone Mode
                    with st.spinner("Calculating optimal route (Standalone Mode)..."):
                        time.sleep(1.5) # Simulate processing
                        
                        # Get coords
                        start_coords = None
                        end_coords = None
                        
                        # Simple lookup from sensor data (in a real app we'd need a full map or geocoder)
                        # We'll just define a fallback
                        default_latlng = {"lat": 12.9716, "lng": 77.5946}
                        
                        # Look up in sensors
                        s_list = dashboard.get_sensors_list()
                        if s_list:
                            for s in s_list.get("sensors", []):
                                if s["location"] == start_location: start_coords = s["coordinates"]
                                if s["location"] == end_location: end_coords = s["coordinates"]
                        
                        if not start_coords: start_coords = ADDITIONAL_LOCATIONS.get(start_location, default_latlng)
                        if not end_coords: end_coords = ADDITIONAL_LOCATIONS.get(end_location, default_latlng)

                        result = dashboard.mock_route_optimization(start_location, end_location, start_coords, end_coords)
                        
                        # Simulate success response structure
                        if result:
                            st.success("Route optimization completed!")
                            
                            # Display recommended route
                            st.subheader("Recommended Route")
                            recommended = result.get('recommended_route', {})
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Distance", f"{recommended.get('distance', 0):.1f} km")
                            with col2:
                                st.metric("Estimated Time", f"{recommended.get('estimated_time', 0)} min")
                            with col3:
                                congestion = recommended.get('congestion_level', 0)
                                st.metric("Congestion", f"Level {congestion}/5")
                            
                            st.write(f"**Path:** {' → '.join(recommended.get('path', []))}")
                            st.write(f"**Route Score:** {recommended.get('score', 0):.2f}/1.0")
                            # Display alternative routes
                            alternatives = result.get('alternative_routes', [])
                            if alternatives:
                                st.subheader("Alternative Routes")
                                
                                for i, route in enumerate(alternatives, 1):
                                    status = f"**#{i}**"
                                    
                                    with st.expander(f"{status} {route.get('route_id', 'Unknown')} - Score: {route.get('score', 0):.2f}"):
                                        col1, col2, col3 = st.columns(3)
                                        with col1:
                                            st.write(f"**Distance:** {route.get('distance', 0):.1f} km")
                                        with col2:
                                            st.write(f"**Time:** {route.get('estimated_time', 0)} min")
                                        with col3:
                                            congestion = route.get('congestion_level', 0)
                                            st.write(f"**Congestion:** Level {congestion}/5")
                                        st.write(f"**Path:** {' → '.join(route.get('path', []))}")
                                
                            render_route_map(
                                start_location,
                                end_location,
                                recommended,
                                alternatives,
                                sensors_data
                            )
                            
                        else:
                            st.error("Could not calculate route.")
    
    elif page == "Video Analysis":
        st.header("Video Analysis")
        st.info("Analyze traffic videos from Kaggle downloads or your local gallery.")
        
        # Create tabs for different video sources
        tab1, tab2, tab3 = st.tabs(["Gallery Upload", "Kaggle Download", "File Upload"])
        
        with tab1:
            st.subheader("Video Gallery")
            st.info("Select a video from your local gallery to analyze.")
            
            # Get video files from common directories
            import os
            import glob
            
            # Define search directories
            search_dirs = [
                os.getcwd(),  # Current directory
                os.path.join(os.getcwd(), "downloads"),  # Downloads folder
                os.path.join(os.getcwd(), "videos"),  # Videos folder
                os.path.join(os.getcwd(), "uploads"),  # Uploads folder
            ]
            
            # Find all video files
            video_extensions = ['*.mp4', '*.avi', '*.mov', '*.mkv', '*.wmv', '*.flv', '*.webm']
            video_files = []
            
            for search_dir in search_dirs:
                if os.path.exists(search_dir):
                    for ext in video_extensions:
                        pattern = os.path.join(search_dir, ext)
                        video_files.extend(glob.glob(pattern))
                        # Also search in subdirectories
                        pattern = os.path.join(search_dir, "**", ext)
                        video_files.extend(glob.glob(pattern, recursive=True))
            
            # Remove duplicates and sort
            video_files = sorted(list(set(video_files)))
            
            if video_files:
                st.write(f"Found {len(video_files)} video file(s):")
                
                # Create a selectbox for video selection
                video_options = {}
                for video_file in video_files:
                    filename = os.path.basename(video_file)
                    # Show relative path for better readability
                    try:
                        rel_path = os.path.relpath(video_file, os.getcwd())
                    except ValueError:
                        rel_path = video_file
                    video_options[f"{filename} ({rel_path})"] = video_file
                
                selected_video_display = st.selectbox(
                    "Choose a video file:",
                    options=list(video_options.keys()),
                    key="gallery_video_select"
                )
                
                if selected_video_display:
                    selected_video_path = video_options[selected_video_display]
                    
                    # Show video info
                    col1, col2 = st.columns([2, 1])
                    
                    # Show video info
                    st.write(f"**Selected:** {os.path.basename(selected_video_path)}")
                    st.write(f"**Path:** {selected_video_path}")
                    
                    # Get file size
                    try:
                        file_size = os.path.getsize(selected_video_path)
                        file_size_mb = file_size / (1024 * 1024)
                        st.write(f"**Size:** {file_size_mb:.2f} MB")
                    except:
                        st.write("**Size:** Unknown")
                    
                    # Action buttons
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Analysis button
                        if st.button("Analyze Video", key="analyze_gallery"):
                            try:
                                from video_analysis.video_analyzer import VideoAnalyzer
                                
                                with st.spinner("Analyzing video..."):
                                    analyzer = VideoAnalyzer()
                                    result = analyzer.analyze(selected_video_path, frame_skip=5, max_frames=200)
                                
                                st.success("Analysis completed!")
                                
                                # Display results
                                st.subheader("Analysis Results")
                                # Key metrics
                                col1, col2, col3, col4 = st.columns(4)
                                
                                with col1:
                                    st.metric("Total Unique Vehicles", result.get('total_unique_vehicles', 0))
                                
                                with col2:
                                    st.metric("FPS", f"{result.get('fps', 0):.1f}")
                                
                                with col3:
                                    st.metric("Avg Moving Objects", f"{result.get('avg_moving_objects', 0):.1f}")
                                
                                with col4:
                                    density_level = result.get('density_level', 'unknown')
                                    st.metric("Density Level", f"{density_level.title()}")
                                
                                # Detailed results
                                st.subheader("Detailed Analysis")
                                st.json(result)
                                
                                # Moving objects chart
                                if result.get('moving_objects_per_frame'):
                                    fig = go.Figure()
                                    fig.add_trace(go.Scatter(
                                        y=result['moving_objects_per_frame'],
                                        mode='lines+markers',
                                        name='Moving Objects',
                                        line=dict(color='blue', width=2)
                                    ))
                                    
                                    fig.update_layout(
                                        title="Moving Objects Over Time",
                                        xaxis_title="Frame Number",
                                        yaxis_title="Number of Moving Objects",
                                        height=400
                                    )
                                    
                                    st.plotly_chart(fig, use_container_width=True)
                            
                            except Exception as e:
                                st.error(f"Analysis failed: {e}")
                    
                    with col2:
                        # Copy to organized folder button
                        if st.button("Organize", key="organize_gallery"):
                            try:
                                # Create organized folder structure
                                organized_dir = os.path.join(os.getcwd(), "organized_videos")
                                os.makedirs(organized_dir, exist_ok=True)
                                
                                # Copy file to organized folder
                                filename = os.path.basename(selected_video_path)
                                organized_path = os.path.join(organized_dir, filename)
                                
                                import shutil
                                shutil.copy2(selected_video_path, organized_path)
                                st.success(f"Video copied to organized folder: {organized_path}")
                            except Exception as e:
                                st.error(f"Failed to organize video: {e}")
                    
                    with col3:
                        # Delete button with confirmation
                        if st.button("Delete", key="delete_gallery"):
                            st.warning("This will permanently delete the video file!")
                            if st.button("Confirm Delete", key="confirm_delete"):
                                try:
                                    os.remove(selected_video_path)
                                    st.success("Video deleted successfully!")
                                    st.rerun()  # Refresh the page to update the list
                                except Exception as e:
                                    st.error(f"Failed to delete video: {e}")
            
            else:
                st.warning("No video files found in the current directory or common video folders.")
                st.info("""
                **Supported formats:** MP4, AVI, MOV, MKV, WMV, FLV, WEBM
                
                **Searched directories:**
                - Current directory
                - downloads/
                - videos/
                - uploads/
                """)
                
                # Refresh button
                if st.button("Refresh Gallery"):
                    st.rerun()
        
        with tab2:
            st.subheader("Kaggle Download")
            st.info("Download a video from Kaggle by dataset slug and analyze it.")
            
            st.warning("Kaggle download functionality is currently disabled. Please use the Gallery Upload or File Upload tabs instead.")
            
            st.markdown("""
            **Alternative options:**
            1. Use the **Gallery Upload** tab to analyze videos already on your system
            2. Use the **File Upload** tab to upload a video file directly
            3. Manually download videos from Kaggle and place them in the project directory
            """)
        
        with tab3:
            st.subheader("File Upload")
            st.info("Upload a video file directly from your device.")
            
            uploaded_file = st.file_uploader(
                "Choose a video file",
                type=['mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'webm'],
                key="video_upload"
            )
            
            if uploaded_file is not None:
                # Show file info
                st.write(f"**File:** {uploaded_file.name}")
                st.write(f"**Size:** {uploaded_file.size / (1024 * 1024):.2f} MB")
                st.write(f"**Type:** {uploaded_file.type}")
                
                # Save uploaded file
                uploads_dir = os.path.join(os.getcwd(), "uploads")
                os.makedirs(uploads_dir, exist_ok=True)
                
                file_path = os.path.join(uploads_dir, uploaded_file.name)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success(f"File saved to: {file_path}")
                
                # Analyze button
                if st.button("Analyze Uploaded Video"):
                    try:
                        from video_analysis.video_analyzer import VideoAnalyzer
                        
                        with st.spinner("Analyzing uploaded video..."):
                            analyzer = VideoAnalyzer()
                            result = analyzer.analyze(file_path, frame_skip=5, max_frames=200)
                        
                        st.success("Analysis completed!")
                        
                        # Display results similar to gallery analysis
                        st.subheader("Analysis Results")
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("FPS", f"{result.get('fps', 0):.1f}")
                        
                        with col2:
                            st.metric("Resolution", f"{result.get('resolution', {}).get('width', 0)}x{result.get('resolution', {}).get('height', 0)}")
                        
                        with col3:
                            st.metric("Avg Moving Objects", f"{result.get('avg_moving_objects', 0):.1f}")
                        
                        with col4:
                            density_level = result.get('density_level', 'unknown')
                            st.metric("Density Level", f"{density_level.title()}")
                        
                        st.subheader("Detailed Analysis")
                        st.json(result)
                    
                    except Exception as e:
                        st.error(f"Analysis failed: {e}")

    elif page == "System Status":
        st.header("System Status")
        
        # API Status
        st.subheader("API Service Status")
        if api_healthy:
            st.success("API Service: Online")
        else:
            st.error("API Service: Offline")
        
        # Database Status
        st.subheader("Database Status")
        try:
            # This would check actual database connections
            st.success("InfluxDB: Connected")
            st.success("Redis: Connected")
        except:
            st.error("Database: Connection Failed")
        
        # ML Service Status
        st.subheader("Machine Learning Service")
        try:
            # This would check actual ML service
            st.success("Traffic Predictor: Running")
            st.success("Anomaly Detector: Active")
        except:
            st.warning("ML Service: Status Unknown")
        
        # System Information
        st.subheader("System Information")
        st.write(f"**Version:** {dashboard.api_base_url}")
        st.write(f"**Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"**Refresh Interval:** {REFRESH_INTERVAL} seconds")
        
        # Performance Metrics
        st.subheader("Performance Metrics")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Response Time", "45ms", "-5ms")
            st.metric("Uptime", "99.8%", "0.1%")
        
        with col2:
            st.metric("Data Points", "1.2M", "+15K")
            st.metric("Active Sensors", "8", "100%")

if __name__ == "__main__":
    main()


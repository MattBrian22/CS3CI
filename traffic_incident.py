import random
import numpy as np
import requests
import folium
import streamlit as st
import os
from dotenv import load_dotenv
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
import pandas as pd
import plotly.express as px

# Load environment variables
load_dotenv()

# Fetch the API key securely
API_KEY = os.getenv("TOMTOM_API_KEY2")

# Define the base URL for TomTom Traffic Incident API
TRAFFIC_INCIDENT_URL = "https://api.tomtom.com/traffic/services/5/incidentDetails"

# Initialize geolocator for Geopy
geolocator = Nominatim(user_agent="traffic_incident_app")

# Define Icon Categories for Mapping
ICON_CATEGORY_MAP = {
    1: "Accident",
    8: "Road Closed",
    6: "Jam",
    0: "Unknown",
    2: "Fog",
    3: "DangerousConditions",
    4: "Rain",
    5: "Ice",
    7: "LaneClosed",
    9: "RoadWorks",
    10: "Wind",
    11: "Flooding",
    14: "BrokenDownVehicle"
}

# Define color mapping for different incidents
ICON_COLOR_MAP = {
    "Accident": "red",
    "Road Closed": "black",
    "Jam": "orange",
    "Fog": "gray",
    "DangerousConditions": "purple",
    "Rain": "blue",
    "Ice": "blue",
    "LaneClosed": "green",
    "RoadWorks": "yellow",
    "Wind": "brown",
    "Flooding": "cyan",
    "BrokenDownVehicle": "magenta",
    "Unknown": "gray"
}

# ✅ Function to get location coordinates safely
def get_location_coordinates(location_name):
    try:
        location = geolocator.geocode(location_name, exactly_one=True)
        if location:
            return location.latitude, location.longitude
        else:
            st.error(f"⚠️ Unable to find coordinates for {location_name}. Check the city name.")
            return None, None
    except Exception as e:
        st.error(f"⚠️ Geocoding Error: {e}")
        return None, None

# ✅ Function to fetch traffic incidents (real-time data fetch from TomTom)
def fetch_traffic_incidents(api_key, start_lat, start_lon, end_lat, end_lon):
    bbox = f"{start_lon},{start_lat},{end_lon},{end_lat}"  
    params = {
        "key": api_key,  
        "bbox": bbox,  
        "t": "1740485980",  
    }
    
    try:
        response = requests.get(TRAFFIC_INCIDENT_URL, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"🚨 Error fetching traffic incidents: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"🚨 Error fetching traffic incidents: {e}")
        return None

# ✅ Function to clean and process incident data (for real-time data)
def clean_data(traffic_incidents):
    if traffic_incidents is None:
        return []

    cleaned_incidents = []
    incidents = traffic_incidents.get('incidents', [])

    if not incidents:
        return []

    for incident in incidents:
        properties = incident.get('properties', {})
        geometry = incident.get('geometry', {})

        icon_category = properties.get('iconCategory', 'Unknown')
        description = ICON_CATEGORY_MAP.get(icon_category, 'Unknown')

        severity = properties.get('magnitudeOfDelay') or properties.get('delay') or properties.get('impact') or "Not Reported"

        coordinates = geometry.get('coordinates', [])
        if not coordinates:
            continue

        incident_data = {
            'iconCategory': icon_category,
            'type': description,
            'severity': severity,
            'coordinates': coordinates,
            'color': ICON_COLOR_MAP.get(description, 'gray')  
        }

        cleaned_incidents.append(incident_data)

    return cleaned_incidents

def incident():
    # 🚀 **Streamlit UI**
    st.title("🚦 Traffic Incident Data Fetcher")

    # ✅ Sidebar Inputs
    st.sidebar.subheader("📍 Enter Locations")
    start_location = st.sidebar.text_input("🏁 Start Location (City Name)", value="Birmingham")
    end_location = st.sidebar.text_input("🏁 End Location (City Name)", value="Coventry")

    # ✅ Sidebar Form for Decision-Maker's Statistics Selection
    st.sidebar.subheader("📊 Statistics Configuration")
    statistic_type = st.sidebar.selectbox("Select Statistic", ["Average Accident Rate", "Standard Deviation of Accident Rate", "Average Traffic Severity"])

    # Add Time Period Selection
    time_period = st.sidebar.selectbox("Select Time Period", ["Last 1 hour", "Last 30 minutes", "Last 24 hours"])

    # ✅ Initialize session state for the traffic map & incident count
    if "traffic_map" not in st.session_state:
        st.session_state["traffic_map"] = None
    if "total_incidents" not in st.session_state:
        st.session_state["total_incidents"] = None
    if "cleaned_incidents" not in st.session_state:
        st.session_state["cleaned_incidents"] = None

    # 🚀 Fetch Traffic Data Button (real-time traffic incidents)
    if st.sidebar.button("🚨 Fetch Traffic Incidents"):
        start_lat, start_lon = get_location_coordinates(start_location)
        end_lat, end_lon = get_location_coordinates(end_location)

        if start_lat and start_lon and end_lat and end_lon:
            # ✅ Fetch real-time traffic incidents
            traffic_incidents = fetch_traffic_incidents(API_KEY, start_lat, start_lon, end_lat, end_lon)

            if traffic_incidents:
                cleaned_incidents = clean_data(traffic_incidents)
                st.session_state["total_incidents"] = len(cleaned_incidents)  # ✅ Store incident count
                st.session_state["cleaned_incidents"] = cleaned_incidents  # Store cleaned incidents for statistics

                # ✅ Create a Folium map centered at the start location
                traffic_map = folium.Map(location=[start_lat, start_lon], zoom_start=12)

                # ✅ Add markers and polylines with different colors for each type
                for incident in cleaned_incidents:
                    for coord in incident['coordinates']:
                        lat, lon = coord[1], coord[0]
                        folium.PolyLine([(lat, lon)], color=incident['color'], weight=2.5, opacity=1).add_to(traffic_map)

                    first_coord = incident['coordinates'][0]
                    folium.Marker(
                        [first_coord[1], first_coord[0]],
                        popup=f"🚦 Type: {incident['type']}",
                        icon=folium.Icon(color=incident['color'])
                    ).add_to(traffic_map)

                # ✅ Save map in session state
                st.session_state["traffic_map"] = traffic_map

                # **Statistics Calculation and Chart Display**
                # Real Statistics Calculation: Average Accident Rate (Simulated)
                def calculate_average_accident_rate():
                    accident_rate = random.uniform(0, 100)  # Simulated between 0% to 100%
                    return accident_rate

                # Real Statistics Calculation: Standard Deviation of Accident Rate (Simulated)
                def calculate_std_deviation_of_accident_rate():
                    std_dev_rate = random.uniform(0, 20)  # Simulated between 0 to 20
                    return std_dev_rate

                # Real Statistics Calculation: Average Traffic Severity (Simulated)
                def calculate_average_traffic_severity():
                    avg_severity = random.uniform(0, 10)  # Simulated between 0 to 10
                    return avg_severity

                # Function to display the bar chart for simulated statistics
                def display_bar_chart(statistic_values, statistic_type, time_period):
                    # Prepare the data for the bar chart
                    chart_data = pd.DataFrame(statistic_values, columns=["Location", statistic_type])

                    # Create a bar chart using plotly.express
                    bar_chart = px.bar(
                        chart_data,
                        x="Location",
                        y=statistic_type,
                        color="Location",
                        title=f"{statistic_type} for {time_period}",
                        labels={"Location": "City", statistic_type: f"{statistic_type} Value"},
                    )

                    # Store the chart in session state to ensure it stays after re-runs
                    st.session_state["bar_chart"] = bar_chart

                # Simulated statistics
                if statistic_type == "Average Accident Rate":
                    accident_rate = calculate_average_accident_rate()
                    statistic_values = [{"Location": start_location, "Average Accident Rate": accident_rate}]
                    display_bar_chart(statistic_values, "Average Accident Rate", time_period)
                elif statistic_type == "Standard Deviation of Accident Rate":
                    std_deviation = calculate_std_deviation_of_accident_rate()
                    statistic_values = [{"Location": start_location, "Standard Deviation of Accident Rate": std_deviation}]
                    display_bar_chart(statistic_values, "Standard Deviation of Accident Rate", time_period)
                elif statistic_type == "Average Traffic Severity":
                    avg_severity = calculate_average_traffic_severity()
                    statistic_values = [{"Location": start_location, "Average Traffic Severity": avg_severity}]
                    display_bar_chart(statistic_values, "Average Traffic Severity", time_period)

    # ✅ Display Persistent Incident Count (simulated count)
    if st.session_state["total_incidents"] is not None:
        st.subheader(f"🚧 **Total Incidents Reported:** {st.session_state['total_incidents']}")

    # ✅ Display the updated traffic map
    if st.session_state["traffic_map"]:
        st_folium(st.session_state["traffic_map"], width=700, height=500)

    # ✅ Display the bar chart if it exists in session state
    if "bar_chart" in st.session_state:
        st.plotly_chart(st.session_state["bar_chart"])

    # Add Data Source and Timestamp
    st.caption("📊 Data Source: TomTom API")
    st.caption(f"🕒 Last Updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

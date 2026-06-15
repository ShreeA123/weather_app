import streamlit as st
import folium
from streamlit_folium import st_folium
import os
import sys

# Ensure the directory of this file is in Python's path for module resolution
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import scrapper
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

# Set page config
st.set_page_config(
    page_title="South India Weather Portal",
    page_icon="⛈️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to match weather25.com color palette and modern design
st.markdown("""
<style>
    /* Custom page background */
    .stApp {
        background-color: #f7f9fc;
    }
    
    /* Top banner */
    .header-banner {
        background: linear-gradient(135deg, #1353bb 0%, #005eff 100%);
        color: white;
        padding: 1.8rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0, 94, 255, 0.15);
        text-align: center;
    }
    
    .header-banner h1 {
        margin: 0;
        font-size: 2.4rem;
        font-weight: 700;
        color: white !important;
    }
    
    .header-banner p {
        margin: 8px 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    
    /* Cards and containers */
    .weather-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
        margin-bottom: 1rem;
    }
    
    /* Grid for current conditions */
    .conditions-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        margin-top: 1rem;
    }
    
    .condition-box {
        background-color: #f8fafc;
        border: 1px solid #edf2f7;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    
    .condition-label {
        font-size: 0.8rem;
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    
    .condition-value {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1e293b;
    }
    
    /* Timeline day card */
    .day-card {
        background-color: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        height: 100%;
    }
    
    .day-card.current {
        border: 2px solid #005eff;
        background-color: #f0f7ff;
    }
    
    .day-date {
        font-size: 0.9rem;
        font-weight: 600;
        color: #475569;
        margin-bottom: 6px;
    }
    
    .day-temp {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0f172a;
        margin: 5px 0;
    }
    
    .day-desc {
        font-size: 0.8rem;
        color: #64748b;
        height: 32px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# List of 30 Major Cities in India mapped to weather25 URLs
LOCATIONS = {
    "Bengaluru": {
        "lat": 12.9716, "lng": 77.5946,
        "url": "https://www.weather25.com/asia/india/karnataka/bangalore",
        "description": "Bengaluru (Silicon Valley, Karnataka)"
    },
    "Chennai": {
        "lat": 13.0827, "lng": 80.2707,
        "url": "https://www.weather25.com/asia/india/tamil-nadu/chennai",
        "description": "Chennai (Gateway to the South, Tamil Nadu)"
    },
    "Hyderabad": {
        "lat": 17.3850, "lng": 78.4867,
        "url": "https://www.weather25.com/asia/india/andhra-pradesh/hyderabad",
        "description": "Hyderabad (City of Pearls, Telangana)"
    },
    "Coimbatore": {
        "lat": 11.0168, "lng": 76.9558,
        "url": "https://www.weather25.com/asia/india/tamil-nadu/coimbatore",
        "description": "Coimbatore (Manchester of the South, Tamil Nadu)"
    },
    "Madurai": {
        "lat": 9.9252, "lng": 78.1198,
        "url": "https://www.weather25.com/asia/india/tamil-nadu/madurai",
        "description": "Madurai (Temple City, Tamil Nadu)"
    },
    
}

def find_nearest_location(lat, lng):
    min_dist = float('inf')
    closest_name = "Bengaluru"
    for name, coords in LOCATIONS.items():
        # Simple Euclidean distance is sufficient for localized points
        dist = math.sqrt((coords['lat'] - lat)**2 + (coords['lng'] - lng)**2)
        if dist < min_dist:
            min_dist = dist
            closest_name = name
    return closest_name

# Initialize session state for selected city/location
if "selected_city" not in st.session_state:
    st.session_state.selected_city = "Bengaluru"

# Header Banner
st.markdown("""
<div class="header-banner">
    <h1>🌤️ India Weather Portal</h1>
    <p>Real-time data scraped from weather25.com. Click anywhere on the map of India to view reports.</p>
</div>
""", unsafe_allow_html=True)

# Split view layout: Map on the left, Weather reports on the right
left_col, right_col = st.columns([1.1, 1.0])

with left_col:
    st.markdown('<div class="weather-card">', unsafe_allow_html=True)
    st.subheader("🗺️ India Interactive Map")
    st.caption("Click any marker or any part of the land to dynamically update the split-view report.")
    
    # Initialize map state in session state centered on India to prevent resetting center/zoom on redraw
    if "map_center" not in st.session_state:
        st.session_state.map_center = [21.5, 78.5]
    if "map_zoom" not in st.session_state:
        st.session_state.map_zoom = 5.0
        
    # Create folium map centered using persistent state
    m = folium.Map(
        location=st.session_state.map_center, 
        zoom_start=st.session_state.map_zoom, 
        tiles="CartoDB positron",
        control_scale=True
    )
    
    # Add markers for all representative locations
    for name, coords in LOCATIONS.items():
        tooltip_html = f"<b>{name}</b><br>{coords['description']}"
        folium.Marker(
            [coords['lat'], coords['lng']],
            tooltip=tooltip_html,
            popup=name,
            icon=folium.Icon(color="blue", icon="cloud", prefix="fa")
        ).add_to(m)
        
    # Render map in Streamlit
    map_data = st_folium(m, width="100%", height=560, key="south_india_map")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Track map navigation state so it stays where the user pans/zooms
    if map_data:
        if map_data.get("center"):
            st.session_state.map_center = [map_data["center"].get("lat", 21.5), map_data["center"].get("lng", 78.5)]
        if map_data.get("zoom"):
            st.session_state.map_zoom = map_data["zoom"]
            
    # Check if user clicked anywhere on the map background or directly on a marker pin
    click_lat, click_lng = None, None
    if map_data:
        # Prioritize marker click (last_object_clicked)
        if map_data.get("last_object_clicked"):
            click_lat = map_data["last_object_clicked"].get("lat")
            click_lng = map_data["last_object_clicked"].get("lng")
        # Fallback to background click (last_clicked)
        elif map_data.get("last_clicked"):
            click_lat = map_data["last_clicked"].get("lat")
            click_lng = map_data["last_clicked"].get("lng")
            
    if click_lat is not None and click_lng is not None:
        # Bounding box for India region clicks to ignore accidental clicks outside India boundaries
        if 5.0 <= click_lat <= 36.5 and 68.0 <= click_lng <= 98.0:
            closest_location = find_nearest_location(click_lat, click_lng)
            if closest_location != st.session_state.selected_city:
                st.session_state.selected_city = closest_location
                st.rerun()

# Fetch and cache weather data to make tab switching snappy
@st.cache_data(ttl=600)
def get_cached_weather(url, city_name):
    return scrapper.get_weather_from_url(url, city_name)

with right_col:
    selected_name = st.session_state.selected_city
    selected_data = LOCATIONS[selected_name]
    
    st.markdown(f"### 📍 Report: {selected_name}")
    st.markdown(f"*Representative area: {selected_data['description']}*")
    
    # Fetch data with loading spinner
    with st.spinner("Scraping weather data from weather25.com..."):
        try:
            weather_report = get_cached_weather(selected_data['url'], selected_name)
            
            # Create tabs in split view
            tab1, tab2, tab3 = st.tabs(["⚡ Current Weather", "📅 5-Day Trend", "📊 Climate Averages"])
            
            with tab1:
                # Layout current conditions card
                st.markdown(f"""
                <div class="weather-card">
                    <div style="display: flex; align-items: center; justify-content: space-between;">
                        <div>
                            <span style="font-size: 3.5rem; font-weight: 800; color: #005eff;">{weather_report['temp_C']}°C</span>
                            <div style="font-size: 1.2rem; font-weight: 600; color: #475569; margin-top: 5px;">{weather_report['description']}</div>
                            <div style="font-size: 0.85rem; color: #64748b; margin-top: 5px;">Recorded Local Date: {weather_report['date']}</div>
                        </div>
                        <img src="{weather_report['icon_url']}" style="width: 100px; height: 100px; filter: drop-shadow(2px 4px 6px rgba(0,0,0,0.1));" alt="Weather status"/>
                    </div>
                    <hr style="border: 0; border-top: 1px solid #e2e8f0; margin: 1.2rem 0;"/>
                    <div class="conditions-grid">
                        <div class="condition-box">
                            <div class="condition-label">💧 Humidity</div>
                            <div class="condition-value">{weather_report['humidity']}%</div>
                        </div>
                        <div class="condition-box">
                            <div class="condition-label">🌧️ Rain Chance</div>
                            <div class="condition-value">{weather_report['precip_chance']}%</div>
                        </div>
                        <div class="condition-box">
                            <div class="condition-label">💨 Wind Speed</div>
                            <div class="condition-value">{weather_report['wind_speed']} Km/h</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-around; margin-top: 1.2rem; font-size: 0.9rem; color: #475569;">
                        <div>🌅 <b>Sunrise:</b> {weather_report['sunrise']}</div>
                        <div>🌇 <b>Sunset:</b> {weather_report['sunset']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            with tab2:
                st.markdown('<div class="weather-card">', unsafe_allow_html=True)
                st.subheader("📅 5-Day Chronological Trend")
                st.caption("Includes previous 2 days (historical/simulated), current day, and next 2 days (forecast).")
                st.write("")
                
                # Setup 5 columns for the 5-day view
                t_cols = st.columns(5)
                
                # Days 1 & 2: Past weather (2 days ago, yesterday)
                past_days = weather_report.get('past_weather', [])
                for idx, p_day in enumerate(past_days):
                    dt_obj = datetime.strptime(p_day['date'], '%Y-%m-%d')
                    nice_date_str = dt_obj.strftime('%a, %d %b')
                    with t_cols[idx]:
                        label = "2 Days Ago" if idx == 0 else "Yesterday"
                        st.markdown(f"""
                        <div class="day-card">
                            <div style="font-size: 0.75rem; font-weight: 700; color: #ef4444; text-transform: uppercase;">{label}</div>
                            <div class="day-date">{nice_date_str}</div>
                            <img src="{p_day['icon_url']}" style="width: 50px; height: 50px;" alt=""/>
                            <div class="day-temp">{p_day['temp_C']}°C</div>
                            <div class="day-desc">{p_day['description']}</div>
                            <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 8px;">
                                🌧️ {p_day['precip_chance']}% | 💧 {p_day['humidity']}%
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # Day 3: Today
                dt_today = datetime.strptime(weather_report['date'], '%Y-%m-%d')
                nice_today_str = dt_today.strftime('%a, %d %b')
                with t_cols[2]:
                    st.markdown(f"""
                    <div class="day-card current">
                        <div style="font-size: 0.75rem; font-weight: 700; color: #005eff; text-transform: uppercase;">Today</div>
                        <div class="day-date">{nice_today_str}</div>
                        <img src="{weather_report['icon_url']}" style="width: 50px; height: 50px;" alt=""/>
                        <div class="day-temp">{weather_report['temp_C']}°C</div>
                        <div class="day-desc">{weather_report['description']}</div>
                        <div style="font-size: 0.7rem; color: #005eff; margin-top: 8px; font-weight: 600;">
                            🌧️ {weather_report['precip_chance']}% | 💧 {weather_report['humidity']}%
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Days 4 & 5: Forecast (tomorrow, day after tomorrow)
                forecast_days = weather_report.get('forecast', [])
                for idx, f_day in enumerate(forecast_days):
                    dt_obj = datetime.strptime(f_day['date'], '%Y-%m-%d')
                    nice_date_str = dt_obj.strftime('%a, %d %b')
                    with t_cols[3 + idx]:
                        label = "Tomorrow" if idx == 0 else "Day After"
                        st.markdown(f"""
                        <div class="day-card">
                            <div style="font-size: 0.75rem; font-weight: 700; color: #22c55e; text-transform: uppercase;">{label}</div>
                            <div class="day-date">{nice_date_str}</div>
                            <img src="{f_day['icon_url']}" style="width: 50px; height: 50px;" alt=""/>
                            <div class="day-temp" style="font-size: 1.1rem; margin: 10px 0 5px 0;">{f_day['temp_max_C']}° / {f_day['temp_min_C']}°</div>
                            <div class="day-desc">{f_day['description']}</div>
                            <div style="font-size: 0.7rem; color: #94a3b8; margin-top: 8px;">
                                🌧️ {f_day['precip_chance']}% | 💧 {f_day['humidity']}%
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                st.markdown('</div>', unsafe_allow_html=True)
                
            with tab3:
                st.markdown('<div class="weather-card">', unsafe_allow_html=True)
                st.subheader("📊 Climate Monthly Averages")
                st.caption(f"Historical average temperatures and rainfall for {selected_name} throughout the year.")
                
                temps = weather_report.get('monthly_averages_temp', [])
                rains = weather_report.get('monthly_averages_rain', [])
                months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                
                if temps and rains and len(temps) == 12 and len(rains) == 12:
                    # Create Plotly climate chart
                    fig = make_subplots(specs=[[{"secondary_y": True}]])
                    
                    # Add temperature line
                    fig.add_trace(
                        go.Scatter(
                            x=months, 
                            y=temps, 
                            name="Average Temp (°C)", 
                            mode='lines+markers',
                            line=dict(color='#ff6d21', width=3),
                            marker=dict(size=8, color='#ffae00')
                        ),
                        secondary_y=False
                    )
                    
                    # Add rainfall bars
                    fig.add_trace(
                        go.Bar(
                            x=months, 
                            y=rains, 
                            name="Average Rainfall (mm)",
                            marker_color='#1353bb',
                            opacity=0.75
                        ),
                        secondary_y=True
                    )
                    
                    # Update layouts
                    fig.update_layout(
                        title_text=f"Climate Graph for {selected_name}",
                        title_font=dict(size=16, family="sans serif", color="#1a202c"),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        plot_bgcolor='white',
                        paper_bgcolor='white',
                        margin=dict(l=20, r=20, t=60, b=20),
                        height=350,
                    )
                    
                    fig.update_xaxes(showgrid=True, gridcolor='#edf2f7', color='#475569')
                    fig.update_yaxes(title_text="Temperature (°C)", showgrid=True, gridcolor='#edf2f7', color='#475569', secondary_y=False)
                    fig.update_yaxes(title_text="Rainfall (mm)", showgrid=False, color='#475569', secondary_y=True)
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("Climate average data is not fully available for this location.")
                    # Fallback text averages if the page is missing them
                    st.info("Typical Southern India Climate: Warm tropical climate with temperatures ranging between 25°C to 38°C. Heavy precipitation is common during the Southwest (June-September) and Northeast (October-December) monsoons.")
                    
                st.markdown('</div>', unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error loading weather details: {str(e)}")
            st.info("Try selecting another city/region on the map.")

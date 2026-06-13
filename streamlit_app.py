import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# Page Configuration & Premium Glowing CSS
# ==========================================
st.set_page_config(page_title="WeatherPro Analytics", page_icon="🌤️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Deep Dark Premium Background */
    .stApp {
        background: linear-gradient(135deg, #020617 0%, #0f172a 100%);
        color: #e2e8f0;
    }
    
    /* 🧊 Glassmorphism & Blue Lightning Glow for Metric Cards */
    div[data-testid="metric-container"] {
        background: rgba(15, 23, 42, 0.4); 
        backdrop-filter: blur(16px); 
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(56, 189, 248, 0.2); 
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), inset 0 0 10px rgba(56, 189, 248, 0.05);
        transition: all 0.3s ease-in-out;
    }
    
    div[data-testid="metric-container"]:hover {
        box-shadow: 0 0 25px rgba(14, 165, 233, 0.5), inset 0 0 15px rgba(56, 189, 248, 0.2);
        transform: translateY(-3px);
        border: 1px solid rgba(56, 189, 248, 0.6);
    }
    
    /* Hide Default Elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Customizing Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        color: #38bdf8 !important; 
        border-bottom: 2px solid #38bdf8 !important;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
    }
    
    /* Smart Alert Box */
    .smart-alert {
        padding: 15px;
        border-radius: 10px;
        background: rgba(56, 189, 248, 0.1);
        border-left: 5px solid #38bdf8;
        margin-bottom: 20px;
        font-weight: 500;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# Session State for App Memory
# ==========================================
if 'search_history' not in st.session_state:
    st.session_state.search_history = []

# ==========================================
# Helper Functions (Caching & Logic)
# ==========================================

@st.cache_data(ttl=86400)
def get_user_location():
    try:
        return requests.get("https://ipapi.co/json/", timeout=5).json().get("city", "London")
    except:
        return "London" 

@st.cache_data(ttl=3600)
def get_coordinates(city_name):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        response = requests.get(url, timeout=5).json()
        if "results" in response and len(response["results"]) > 0:
            data = response["results"][0]
            return data["latitude"], data["longitude"], data["name"], data.get("country", "")
    except:
        return None, None, None, None
    return None, None, None, None

@st.cache_data(ttl=1800)
def get_weather_data(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,surface_pressure&hourly=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max&timezone=auto"
    return requests.get(url).json()

@st.cache_data(ttl=1800)
def get_air_quality(lat, lon):
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi,pm10,pm2_5"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else None

def get_weather_info(code):
    mapping = {
        0: ("Clear Sky", "☀️", "Great day to be outside! Apply sunscreen if you're out for long."),
        1: ("Mainly Clear", "🌤️", "Nice and clear. Enjoy the day!"),
        2: ("Partly Cloudy", "⛅", "A pleasant mix of sun and clouds."),
        3: ("Overcast", "☁️", "It's quite cloudy today."),
        45: ("Foggy", "🌫️", "Drive safely, visibility might be low."),
        51: ("Light Drizzle", "🌦️", "A light jacket or a cap might be good."),
        61: ("Rain", "🌧️", "Don't forget to carry an umbrella! ☔"),
        65: ("Heavy Rain", "⛈️", "Heavy rain expected. Best to stay indoors if possible."),
        71: ("Snow", "❄️", "It's snowing! Bundle up and stay warm. 🧣"),
        95: ("Thunderstorm", "🌩️", "Thunderstorms in the area. Stay indoors and safe!")
    }
    # Fallbacks for similar codes
    if code in [53, 55]: code = 51
    if code in [63]: code = 61
    if code in [73, 75]: code = 71
    if code in [96, 99]: code = 95
    return mapping.get(code, ("Variable", "🌡️", "Weather is shifting. Be prepared."))

def convert_temp(celsius, unit):
    if unit == "°F": return round((celsius * 9/5) + 32, 1)
    return celsius

# ==========================================
# Main Application
# ==========================================

def main():
    # --- Sidebar (Settings & Search) ---
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        temp_unit = st.radio("Temperature Unit:", ["°C", "°F"], horizontal=True)
        
        st.divider()
        st.markdown("## 🌍 Location")
        
        # Search Box
        default_city = get_user_location()
        search_query = st.text_input("Search City:", placeholder=f"e.g., {default_city}")
        
        # History Buttons
        if search_query and search_query not in st.session_state.search_history:
            st.session_state.search_history.insert(0, search_query)
            if len(st.session_state.search_history) > 5: # Keep only last 5
                st.session_state.search_history.pop()

        if st.session_state.search_history:
            st.caption("Recent Searches:")
            for history_city in st.session_state.search_history:
                if st.button(history_city, use_container_width=True):
                    search_query = history_city
                    
        city_to_search = search_query if search_query else default_city
        
        st.divider()
        st.caption("WeatherPro v2.0 | Professional Dashboard")

    # --- Main Dashboard ---
    st.title("☁️ WeatherPro Analytics")
    
    with st.spinner(f"Connecting to satellites for {city_to_search}..."):
        lat, lon, city, country = get_coordinates(city_to_search)
        
        if lat is None or lon is None:
            st.error(f"⚠️ Could not locate '{city_to_search}'. Please check the spelling.")
            return

        weather = get_weather_data(lat, lon)
        aqi_data = get_air_quality(lat, lon)

        if "current" not in weather:
            st.error("⚠️ Connection to weather servers temporarily lost.")
            return

        current = weather["current"]
        daily = weather["daily"]
        
        desc, icon, advice = get_weather_info(current["weather_code"])
        
        # Smart Alert
        st.markdown(f'<div class="smart-alert">💡 <b>Smart Advice:</b> {advice}</div>', unsafe_allow_html=True)
        
        st.markdown(f"### 📍 **{city}, {country}** | {icon} {desc}")
        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs(["📊 Current Overview", "📈 24H Forecast", "📅 7-Day Trend", "🗺️ AQI & Radar"])

        # TAB 1: Current Overview
        with tab1:
            m1, m2, m3, m4 = st.columns(4)
            
            t_val = convert_temp(current['temperature_2m'], temp_unit)
            t_feel = convert_temp(current['apparent_temperature'], temp_unit)
            
            with m1:
                st.metric(label=f"Temperature", value=f"{t_val} {temp_unit}", delta=f"Feels like {t_feel} {temp_unit}")
            with m2:
                st.metric(label="Wind Speed", value=f"{current['wind_speed_10m']} km/h", delta="Normal", delta_color="off")
            with m3:
                st.metric(label="Humidity", value=f"{current['relative_humidity_2m']} %", delta="Moderate", delta_color="off")
            with m4:
                st.metric(label="Pressure", value=f"{current['surface_pressure']} hPa")
            
            st.markdown("<br>#### ☀️ Solar & UV Analytics", unsafe_allow_html=True)
            sr = datetime.strptime(daily['sunrise'][0], "%Y-%m-%dT%H:%M").strftime("%I:%M %p")
            ss = datetime.strptime(daily['sunset'][0], "%Y-%m-%dT%H:%M").strftime("%I:%M %p")
            
            sc1, sc2, sc3 = st.columns(3)
            sc1.info(f"🌅 **Sunrise:** {sr}")
            sc2.info(f"🌇 **Sunset:** {ss}")
            sc3.info(f"☀️ **UV Index (Max):** {daily['uv_index_max'][0]}")

        # TAB 2: Hourly Graph
        with tab2:
            st.markdown("#### Hourly Temperature Trend")
            h_times = [datetime.strptime(t, "%Y-%m-%dT%H:%M").strftime("%I %p") for t in weather["hourly"]["time"][:24]]
            h_temps = [convert_temp(t, temp_unit) for t in weather["hourly"]["temperature_2m"][:24]]
            
            df_hourly = pd.DataFrame({"Time": h_times, f"Temp ({temp_unit})": h_temps})

            fig = px.area(df_hourly, x="Time", y=f"Temp ({temp_unit})", markers=True, color_discrete_sequence=['#38bdf8'])
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(showgrid=False, title=""),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                font=dict(color='#e2e8f0')
            )
            st.plotly_chart(fig, width="stretch")

        # TAB 3: 7-Day Forecast
        with tab3:
            st.markdown("#### Weekly Weather Pattern")
            forecast_data = []
            for i in range(7):
                d_date = datetime.strptime(daily['time'][i], "%Y-%m-%d")
                d_name = d_date.strftime("%A") if i > 0 else "Today"
                d_desc, d_icon, _ = get_weather_info(daily['weather_code'][i])
                
                t_min = convert_temp(daily['temperature_2m_min'][i], temp_unit)
                t_max = convert_temp(daily['temperature_2m_max'][i], temp_unit)
                
                forecast_data.append({
                    "Day": d_name,
                    "Date": d_date.strftime("%d %b"),
                    "Condition": f"{d_icon} {d_desc}",
                    f"Min ({temp_unit})": t_min,
                    f"Max ({temp_unit})": t_max
                })
            
            st.dataframe(pd.DataFrame(forecast_data), width="stretch", hide_index=True)

        # TAB 4: AQI & Map
        with tab4:
            c_aqi, c_map = st.columns([1, 1])
            with c_aqi:
                st.markdown("#### 🍃 Air Quality (AQI)")
                if aqi_data and "current" in aqi_data:
                    aqi_val = aqi_data["current"]["us_aqi"]
                    status, color = ("Good", "normal") if aqi_val < 50 else ("Moderate", "off") if aqi_val < 100 else ("Poor", "inverse")
                    st.metric(label="Current US AQI", value=aqi_val, delta=status, delta_color=color)
                    st.caption(f"**PM 10:** {aqi_data['current'].get('pm10', 'N/A')} | **PM 2.5:** {aqi_data['current'].get('pm2_5', 'N/A')}")
                else:
                    st.warning("AQI data currently unavailable.")
            
            with c_map:
                st.markdown("#### 🗺️ Location Radar")
                st.map(pd.DataFrame({'lat': [lat], 'lon': [lon]}), zoom=11, width="stretch")

if __name__ == "__main__":
    main()
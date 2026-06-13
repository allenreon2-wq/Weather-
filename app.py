import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime

# ==========================================
# Page Configuration & Premium CSS
# ==========================================
st.set_page_config(page_title="WeatherPro Analytics", page_icon="🌤️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
    /* Premium Dark Theme */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    
    /* Clean Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    /* Hide Default Elements for a clean Web App look */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Customizing Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# Helper Functions (With Smart Caching)
# ==========================================

@st.cache_data(ttl=86400) # Caches IP location for a day
def get_user_location():
    """Auto-detect user's city based on IP address."""
    try:
        response = requests.get("https://ipapi.co/json/", timeout=5).json()
        return response.get("city", "London")
    except:
        return "London" # Default fallback

@st.cache_data(ttl=3600)
def get_coordinates(city_name):
    """Fetch Lat/Lon for a given city."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1&language=en&format=json"
        response = requests.get(url, timeout=5).json()
        if "results" in response and len(response["results"]) > 0:
            data = response["results"][0]
            return data["latitude"], data["longitude"], data["name"], data.get("country", "")
    except Exception:
        return None, None, None, None
    return None, None, None, None

@st.cache_data(ttl=1800)
def get_weather_data(lat, lon):
    """Fetch comprehensive weather data."""
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m,surface_pressure&hourly=temperature_2m,precipitation_probability,weather_code&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max&timezone=auto"
    return requests.get(url).json()

@st.cache_data(ttl=1800)
def get_air_quality(lat, lon):
    """Fetch Air Quality Index."""
    url = f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&current=us_aqi,pm10,pm2_5"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

def get_weather_condition(code):
    """Convert WMO weather codes to human-readable text and emojis."""
    weather_mapping = {
        0: ("Clear Sky", "☀️"),
        1: ("Mainly Clear", "🌤️"),
        2: ("Partly Cloudy", "⛅"),
        3: ("Overcast", "☁️"),
        45: ("Foggy", "🌫️"),
        48: ("Depositing Rime Fog", "🌫️"),
        51: ("Light Drizzle", "🌦️"),
        53: ("Moderate Drizzle", "🌧️"),
        55: ("Dense Drizzle", "🌧️"),
        61: ("Slight Rain", "🌧️"),
        63: ("Moderate Rain", "🌧️"),
        65: ("Heavy Rain", "⛈️"),
        71: ("Slight Snow Fall", "🌨️"),
        73: ("Moderate Snow Fall", "❄️"),
        75: ("Heavy Snow Fall", "❄️"),
        95: ("Thunderstorm", "🌩️"),
        96: ("Thunderstorm with Hail", "⛈️"),
        99: ("Heavy Thunderstorm with Hail", "⛈️")
    }
    return weather_mapping.get(code, ("Unknown", "🌡️"))

# ==========================================
# Main App Application
# ==========================================

def main():
    # --- Sidebar Setup ---
    with st.sidebar:
        st.markdown("## 🌍 Location Settings")
        default_city = get_user_location()
        search_query = st.text_input("Enter City Name:", placeholder=f"e.g., {default_city}")
        city_to_search = search_query if search_query else default_city
        
        st.divider()
        st.markdown("### ℹ️ About App")
        st.caption("WeatherPro is a professional meteorological dashboard providing real-time weather analytics, AQI tracking, and 7-day forecasting.")
        st.caption("Developed with ❤️ using Python.")

    # --- Main Screen Setup ---
    st.title("☁️ WeatherPro Analytics Dashboard")
    
    with st.spinner(f"Fetching meteorological data for {city_to_search}..."):
        lat, lon, city, country = get_coordinates(city_to_search)
        
        if lat is None or lon is None:
            st.error(f"⚠️ We couldn't find the city '{city_to_search}'. Please verify the spelling.")
            return

        weather = get_weather_data(lat, lon)
        aqi_data = get_air_quality(lat, lon)

        if "current" not in weather:
            st.error("⚠️ Connection to weather servers lost. Please try again later.")
            return

        current = weather["current"]
        daily = weather["daily"]
        
        # Determine Current Weather Condition
        weather_desc, weather_icon = get_weather_condition(current["weather_code"])
        
        # --- Top Header ---
        st.markdown(f"### 📍 **{city}, {country}** | {weather_icon} {weather_desc}")
        st.caption(f"Coordinates: {lat}° N, {lon}° E")
        st.divider()

        # --- Dashboard Tabs ---
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Current Overview", "📈 Hourly Forecast", "📅 7-Day Forecast", "🗺️ AQI & Map"])

        # TAB 1: Current Overview
        with tab1:
            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric(label="Temperature", value=f"{current['temperature_2m']} °C", delta=f"Feels like {current['apparent_temperature']} °C")
            with m2:
                st.metric(label="Wind Speed", value=f"{current['wind_speed_10m']} km/h", delta="Normal", delta_color="off")
            with m3:
                st.metric(label="Humidity", value=f"{current['relative_humidity_2m']} %", delta="Moderate", delta_color="off")
            with m4:
                st.metric(label="Surface Pressure", value=f"{current['surface_pressure']} hPa")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Sun Cycle Data
            st.markdown("#### ☀️ Sun Cycle Info")
            sunrise_time = datetime.strptime(daily['sunrise'][0], "%Y-%m-%dT%H:%M").strftime("%I:%M %p")
            sunset_time = datetime.strptime(daily['sunset'][0], "%Y-%m-%dT%H:%M").strftime("%I:%M %p")
            
            sc1, sc2, sc3 = st.columns(3)
            sc1.info(f"🌅 **Sunrise:** {sunrise_time}")
            sc2.info(f"🌇 **Sunset:** {sunset_time}")
            sc3.info(f"☀️ **UV Index (Max):** {daily['uv_index_max'][0]}")

        # TAB 2: Hourly Forecast
        with tab2:
            st.markdown("#### 24-Hour Temperature Trend")
            hourly_times = weather["hourly"]["time"][:24]
            hourly_temps = weather["hourly"]["temperature_2m"][:24]
            formatted_times = [datetime.strptime(t, "%Y-%m-%dT%H:%M").strftime("%I %p") for t in hourly_times]
            
            df_hourly = pd.DataFrame({
                "Time": formatted_times,
                "Temperature (°C)": hourly_temps
            })

            fig = px.area(df_hourly, x="Time", y="Temperature (°C)", markers=True, color_discrete_sequence=['#3b82f6'])
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(showgrid=False, title=""),
                yaxis=dict(showgrid=True, gridcolor='#334155'),
                font=dict(color='#e2e8f0')
            )
            st.plotly_chart(fig, use_container_width=True)

        # TAB 3: 7-Day Forecast
        with tab3:
            st.markdown("#### Upcoming Weather Pattern")
            
            # Create a clean dataframe for the 7-day forecast
            forecast_data = []
            for i in range(7):
                day_date = datetime.strptime(daily['time'][i], "%Y-%m-%d")
                day_name = day_date.strftime("%A") if i > 0 else "Today"
                desc, icon = get_weather_condition(daily['weather_code'][i])
                
                forecast_data.append({
                    "Day": day_name,
                    "Date": day_date.strftime("%d %b"),
                    "Condition": f"{icon} {desc}",
                    "Min Temp (°C)": daily['temperature_2m_min'][i],
                    "Max Temp (°C)": daily['temperature_2m_max'][i]
                })
            
            df_forecast = pd.DataFrame(forecast_data)
            # Displaying data as a sleek Streamlit dataframe without the index
            st.dataframe(df_forecast, use_container_width=True, hide_index=True)

        # TAB 4: AQI & Map
        with tab4:
            col_aqi, col_map = st.columns([1, 1])
            
            with col_aqi:
                st.markdown("#### 🍃 Air Quality Analytics")
                if aqi_data and "current" in aqi_data:
                    aqi_val = aqi_data["current"]["us_aqi"]
                    pm10 = aqi_data["current"].get("pm10", "N/A")
                    pm25 = aqi_data["current"].get("pm2_5", "N/A")
                    
                    if aqi_val < 50:
                        status, color = "Good", "normal"
                    elif aqi_val < 100:
                        status, color = "Moderate", "off"
                    else:
                        status, color = "Poor", "inverse"
                        
                    st.metric(label="Current US AQI", value=aqi_val, delta=status, delta_color=color)
                    st.caption(f"**PM 10:** {pm10} μg/m³ | **PM 2.5:** {pm25} μg/m³")
                else:
                    st.warning("Air Quality data is currently unavailable for this region.")
            
            with col_map:
                st.markdown("#### 🗺️ Geographic Location")
                map_data = pd.DataFrame({'lat': [lat], 'lon': [lon]})
                st.map(map_data, zoom=11, use_container_width=True)

if __name__ == "__main__":
    main()
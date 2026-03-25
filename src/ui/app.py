"""
Streamlit Frontend for ClimateGuardAI
"""
import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="ClimateGuardAI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint
API_BASE_URL = "http://localhost:8000"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #2E7D32;
        text-align: center;
        padding: 1rem;
    }
    .risk-high {
        background-color: #FFEBEE;
        border-left: 5px solid #D32F2F;
        padding: 1rem;
        border-radius: 5px;
        color: #1a1a1a;
    }
    .risk-high h2 {
        color: #D32F2F;
        margin-top: 0;
    }
    .risk-medium {
        background-color: #FFF3E0;
        border-left: 5px solid #F57C00;
        padding: 1rem;
        border-radius: 5px;
        color: #1a1a1a;
    }
    .risk-medium h2 {
        color: #F57C00;
        margin-top: 0;
    }
    .risk-low {
        background-color: #E8F5E9;
        border-left: 5px solid #388E3C;
        padding: 1rem;
        border-radius: 5px;
        color: #1a1a1a;
    }
    .risk-low h2 {
        color: #388E3C;
        margin-top: 0;
    }
    .metric-card {
        background-color: #F5F5F5;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        color: #1a1a1a;
    }
    .metric-card h2 {
        color: #1a1a1a;
        margin: 0.5rem 0;
    }
    .metric-card h3 {
        margin-top: 0;
    }
    .metric-card p {
        color: #555;
        margin-bottom: 0;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown('<div class="main-header">🌍 ClimateGuardAI</div>', unsafe_allow_html=True)
st.markdown(
    '<p style="text-align: center; font-size: 1.2rem; color: #666;">Hyperlocal Climate Intelligence & Adaptation Advisory</p>',
    unsafe_allow_html=True
)

# Sidebar
with st.sidebar:
    st.header("📍 Location Settings")
    
    # Preset locations
    location_presets = {
        "Mumbai, Maharashtra": (19.0760, 72.8777),
        "Nashik, Maharashtra": (19.9975, 73.7898),
        "Delhi": (28.6139, 77.2090),
        "Bengaluru, Karnataka": (12.9716, 77.5946),
        "Custom": None
    }
    
    selected_location = st.selectbox(
        "Select Location",
        options=list(location_presets.keys())
    )
    
    if selected_location == "Custom":
        latitude = st.number_input("Latitude", value=19.0760, min_value=-90.0, max_value=90.0, step=0.001)
        longitude = st.number_input("Longitude", value=72.8777, min_value=-180.0, max_value=180.0, step=0.001)
        location_name = st.text_input("Location Name", value="Custom Location")
    else:
        latitude, longitude = location_presets[selected_location]
        location_name = selected_location
    
    st.divider()
    
    st.header("⚙️ Settings")
    forecast_days = st.slider("Forecast Days", min_value=3, max_value=14, value=7)
    include_satellite = st.checkbox("Include Satellite Data", value=True)
    language = st.selectbox("Language", ["en", "hi", "mr", "ta"])
    
    st.divider()
    
    generate_btn = st.button("🚀 Generate Advisory", type="primary", width='stretch')


# Main content
if generate_btn:
    with st.spinner("🔍 Analyzing climate data..."):
        try:
            # Call API
            response = requests.post(
                f"{API_BASE_URL}/advisory/generate",
                json={
                    "latitude": latitude,
                    "longitude": longitude,
                    "location_name": location_name,
                    "forecast_days": forecast_days,
                    "include_satellite": include_satellite,
                    "language": language
                },
                timeout=120  # Increased to 120 seconds for satellite data + AI generation
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Header with risk level
                risk_level = data['risk_level']
                risk_class = f"risk-{risk_level.lower()}"
                
                st.markdown(f"""
                <div class="{risk_class}">
                    <h2>🎯 Risk Level: {risk_level}</h2>
                    <p><strong>Location:</strong> {data['location']['name']}</p>
                    <p><strong>Analysis Time:</strong> {data['timestamp']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                st.divider()
                
                # Weather Forecast Section
                st.header("🌤️ Weather Forecast")
                
                weather = data['weather_forecast']
                
                # Create forecast DataFrame
                forecast_df = pd.DataFrame({
                    'Day': [f"Day {i+1}" for i in range(len(weather['median']))],
                    'Temperature (°C)': weather['median'],
                    'Min Temp': weather['lower_bound'],
                    'Max Temp': weather['upper_bound'],
                    'Humidity (%)': weather['humidity'],
                    'Rainfall (mm)': weather['rainfall']
                })
                
                # Temperature plot
                fig_temp = go.Figure()
                
                fig_temp.add_trace(go.Scatter(
                    x=forecast_df['Day'],
                    y=forecast_df['Temperature (°C)'],
                    mode='lines+markers',
                    name='Temperature',
                    line=dict(color='#FF5722', width=3),
                    marker=dict(size=8)
                ))
                
                fig_temp.add_trace(go.Scatter(
                    x=forecast_df['Day'],
                    y=forecast_df['Max Temp'],
                    mode='lines',
                    name='Max Temp',
                    line=dict(color='#FF5722', width=1, dash='dot'),
                    showlegend=False
                ))
                
                fig_temp.add_trace(go.Scatter(
                    x=forecast_df['Day'],
                    y=forecast_df['Min Temp'],
                    mode='lines',
                    name='Min Temp',
                    line=dict(color='#2196F3', width=1, dash='dot'),
                    fill='tonexty',
                    fillcolor='rgba(255, 87, 34, 0.1)',
                    showlegend=False
                ))
                
                fig_temp.update_layout(
                    title="Temperature Forecast",
                    xaxis_title="Day",
                    yaxis_title="Temperature (°C)",
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig_temp, width='stretch')
                
                # Rainfall and Humidity
                col1, col2 = st.columns(2)
                
                with col1:
                    fig_rain = px.bar(
                        forecast_df,
                        x='Day',
                        y='Rainfall (mm)',
                        title="Rainfall Forecast",
                        color='Rainfall (mm)',
                        color_continuous_scale='Blues'
                    )
                    st.plotly_chart(fig_rain, width='stretch')
                
                with col2:
                    fig_humidity = px.line(
                        forecast_df,
                        x='Day',
                        y='Humidity (%)',
                        title="Humidity Forecast",
                        markers=True
                    )
                    st.plotly_chart(fig_humidity, width='stretch')
                
                st.divider()
                
                # Satellite Data (if available)
                if data.get('satellite_data'):
                    st.header("🛰️ Satellite Analysis")
                    
                    sat_data = data['satellite_data']
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        ndvi = sat_data.get('ndvi', {}).get('mean', 0)
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3 style="color: #4CAF50;">🌱 NDVI</h3>
                            <h2>{ndvi:.3f}</h2>
                            <p>Vegetation Health</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        ndwi = sat_data.get('ndwi', {}).get('mean', 0)
                        st.markdown(f"""
                        <div class="metric-card">
                            <h3 style="color: #2196F3;">💧 NDWI</h3>
                            <h2>{ndwi:.3f}</h2>
                            <p>Water Content</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col3:
                        if 'temperature_celsius' in sat_data:
                            lst = sat_data['temperature_celsius'].get('mean', 0)
                            st.markdown(f"""
                            <div class="metric-card">
                                <h3 style="color: #FF5722;">🌡️ LST</h3>
                                <h2>{lst:.1f}°C</h2>
                                <p>Land Surface Temp</p>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # Interpretation
                    st.info(f"""
                    **Satellite Data Interpretation:**
                    - **NDVI ({ndvi:.3f})**: {'Healthy vegetation' if ndvi > 0.4 else 'Stressed vegetation' if ndvi > 0.2 else 'Poor vegetation'}
                    - **NDWI ({ndwi:.3f})**: {'Good water availability' if ndwi > 0.3 else 'Moderate water' if ndwi > 0.1 else 'Low water content'}
                    """)
                    
                    st.divider()
                
                # AI Advisory
                st.header("🤖 AI-Powered Advisory")
                
                advisory = data['advisory']
                
                # Create tabs for different sections
                tab1, tab2, tab3, tab4, tab5 = st.tabs([
                    "🎯 Risk Assessment",
                    "⚡ Immediate Actions",
                    "🌾 Crop Recommendations",
                    "🚨 Disaster Preparedness",
                    "📈 Long-term Adaptation"
                ])
                
                with tab1:
                    st.markdown(advisory.get('risk_assessment', 'No data available'))
                
                with tab2:
                    st.markdown(advisory.get('immediate_actions', 'No data available'))
                
                with tab3:
                    st.markdown(advisory.get('crop_recommendations', 'No data available'))
                
                with tab4:
                    st.markdown(advisory.get('disaster_preparedness', 'No data available'))
                
                with tab5:
                    st.markdown(advisory.get('long_term_adaptation', 'No data available'))
                
                # Download options
                st.divider()
                st.subheader("📥 Download Options")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    # PDF Report
                    if st.button("📄 Download PDF Report"):
                        st.info("PDF generation feature coming soon!")
                
                with col2:
                    # JSON Data
                    json_str = json.dumps(data, indent=2)
                    st.download_button(
                        label="💾 Download JSON Data",
                        data=json_str,
                        file_name=f"climate_advisory_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
                
                with col3:
                    # Voice Advisory
                    if st.button("🔊 Get Voice Advisory"):
                        with st.spinner("Generating voice advisory..."):
                            voice_response = requests.post(
                                f"{API_BASE_URL}/advisory/voice",
                                json={
                                    "latitude": latitude,
                                    "longitude": longitude,
                                    "location_name": location_name,
                                    "forecast_days": forecast_days,
                                    "include_satellite": include_satellite,
                                    "language": language
                                },
                                timeout=120  # Same timeout as main advisory
                            )
                            
                            if voice_response.status_code == 200:
                                voice_data = voice_response.json()
                                st.success("Voice advisory generated!")
                                st.text_area("Voice Message", voice_data['voice_message'], height=200)
                
            else:
                st.error(f"API Error: {response.status_code} - {response.text}")
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Connection Error: {str(e)}")
            st.info("Make sure the API server is running at http://localhost:8000")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

else:
    # Welcome screen
    st.info("""
    👈 **Get Started:**
    1. Select a location from the sidebar (or enter custom coordinates)
    2. Adjust settings as needed
    3. Click "Generate Advisory" to get your climate intelligence report
    
    **What You'll Get:**
    - 🌤️ 7-day hyperlocal weather forecast
    - 🛰️ Real-time satellite vegetation & water indices
    - 🎯 AI-powered risk assessment
    - 🌾 Personalized crop recommendations
    - 🚨 Early disaster warnings
    - 📱 Voice advisory in your local language
    """)
    
    # Sample visualization
    st.subheader("📊 Sample Climate Trends")
    
    # Create sample data
    sample_dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='ME')  # ME = Month End
    sample_data = pd.DataFrame({
        'Month': sample_dates.strftime('%B'),
        'Temperature': [28, 30, 33, 35, 34, 30, 28, 27, 28, 30, 29, 28],
        'Rainfall': [10, 5, 8, 40, 120, 200, 250, 180, 100, 30, 15, 12]
    })
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=sample_data['Month'],
        y=sample_data['Temperature'],
        name='Temperature (°C)',
        yaxis='y1',
        line=dict(color='#FF5722', width=2)
    ))
    
    fig.add_trace(go.Bar(
        x=sample_data['Month'],
        y=sample_data['Rainfall'],
        name='Rainfall (mm)',
        yaxis='y2',
        marker=dict(color='#2196F3')
    ))
    
    fig.update_layout(
        title="Typical Annual Climate Pattern",
        xaxis=dict(title='Month'),
        yaxis=dict(title='Temperature (°C)', side='left'),
        yaxis2=dict(title='Rainfall (mm)', overlaying='y', side='right'),
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, width='stretch')

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🌍 <strong>ClimateGuardAI</strong> - ET GenAI Hackathon 2025</p>
    <p>Built using Claude AI, Satellite Data & Weather APIs</p>
</div>
""", unsafe_allow_html=True)
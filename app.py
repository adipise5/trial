import streamlit as st
import requests
from PIL import Image
import numpy as np
import joblib
import os
import io
from tensorflow.keras.preprocessing import image as keras_image
import plotly.express as px
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Must be the first Streamlit command
st.set_page_config(page_title="Bhoomi Dashboard", layout="wide", initial_sidebar_state="expanded")

# xAI API Key from environment variable
XAI_API_KEY = os.getenv("XAI_API_KEY", "xai-Es0CPO6ARiKBHkmHpO4PdiMGFJUjDDqFq6mNWJeQVLdeF8bv9SpezkYC0nQCC9R3tZChgopAQME9bpmo")
XAI_API_URL = "https://api.x.ai/v1/completions"  # Hypothetical URL; replace with actual endpoint

# Load ML models with caching and error handling
@st.cache_resource
def load_model(model_path):
    try:
        return joblib.load(model_path)
    except FileNotFoundError:
        st.error(f"Model file not found: {model_path}")
        return None

crop_model = load_model('models/crop_recommendation.pkl')
yield_model = None  # Placeholder
fertilizer_model = None  # Placeholder

# Placeholder for disease model
@st.cache_resource
def load_disease_model():
    return None

disease_model = load_disease_model()

# Weather API function
def get_weather(zip_code, country_code="IN"):
    api_key = "f938f65079af3e9bd2414c6556df724b"
    url = f"http://api.openweathermap.org/geo/1.0/zip?zip={zip_code},{country_code}&appid={api_key}"
    try:
        response = requests.get(url).json()
        if 'lat' not in response or 'lon' not in response:
            return {"error": "Invalid ZIP code or country code"}
        lat, lon = response['lat'], response['lon']
        weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        weather_response = requests.get(weather_url).json()
        return weather_response
    except requests.RequestException:
        return {"error": "Failed to connect to weather service"}

@st.cache_data
def get_smart_farming_info(crop, country):
    try:
        headers = {"Authorization": f"Bearer {XAI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": "grok",
            "prompt": f"Provide detailed smart farming guidelines for {crop} in {country}, including fertilizers, time periods, and best practices.",
            "max_tokens": 500
        }
        response = requests.post(XAI_API_URL, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("choices", [{}])[0].get("text", "No guidance available")
    except Exception as e:
        return f"Error fetching smart farming guidance: {str(e)}"

def predict_disease(image):
    if disease_model is None:
        return "Disease detection model not loaded (placeholder)"
    img = keras_image.img_to_array(image.resize((224, 224))) / 255.0
    img = np.expand_dims(img, axis=0)
    return "Disease Name (placeholder)"

# Custom CSS for modern, aesthetic UI with consistent colors
st.markdown(
    """
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #e8f5e9; /* Light green background */
            color: #2e7d32; /* Dark green text */
        }
        .main {
            padding: 20px;
            max-width: 1200px;
            margin: 0 auto;
        }
        h1, h2, h3, h4, h5, h6 {
            text-align: center;
            color: #2e7d32; /* Dark green for headings */
        }
        .stTextInput>div>input, .stNumberInput>div>input {
            background-color: #c8e6c9; /* Light green input background */
            border: 1px solid #4caf50; /* Medium green border */
            border-radius: 5px;
            padding: 8px;
            color: #2e7d32;
        }
        .stButton>button {
            background-color: #4caf50; /* Medium green button */
            color: white;
            border-radius: 5px;
            padding: 10px 20px;
            border: none;
            width: 100%;
        }
        .stButton>button:hover {
            background-color: #388e3c; /* Darker green on hover */
        }
        .sidebar .sidebar-content {
            background-color: #4caf50; /* Medium green sidebar */
            color: white;
            padding: 20px;
            border-radius: 10px;
        }
        .sidebar .sidebar-content .stButton>button {
            background-color: #388e3c; /* Darker green sidebar buttons */
            margin: 5px 0;
        }
        .sidebar .sidebar-content .stButton>button:hover {
            background-color: #2e7d32; /* Even darker green on hover */
        }
        .card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 20px;
            margin: 10px auto;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            max-width: 300px;
        }
        .card h3 {
            color: #4caf50;
            margin-bottom: 10px;
        }
        .stForm {
            background-color: #ffffff;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            max-width: 600px;
            margin: 0 auto;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# User registration session
if 'user_info' not in st.session_state:
    st.title("🌱 Bhoomi - Farmer Registration")
    with st.form("user_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        mobile = st.text_input("Mobile Number", help="e.g., 9876543210")
        place = st.text_input("Place")
        submitted = st.form_submit_button("Submit")
    if submitted:
        if name and mobile and place:
            st.session_state.user_info = {"name": name, "mobile": mobile, "place": place}
            st.success("Registration successful! Redirecting to dashboard...")
            st.session_state.menu = "Home"
            st.rerun()
        else:
            st.error("Please fill in all fields.")
else:
    st.title(f"🌱 Bhoomi - Welcome {st.session_state.user_info['name']}")
    st.markdown("<p style='text-align: center;'>Your personalized farming dashboard.</p>", unsafe_allow_html=True)

    # Sidebar Navigation
    st.sidebar.title("🌍 Navigation")
    if 'menu' not in st.session_state:
        st.session_state['menu'] = "Home"

    menu_options = {
        "Home": "🏠 Home",
        "Crop Recommendation": "🌾 Crop Recommendation",
        "Identify Plant Disease": "🦠 Identify Plant Disease",
        "Crop Yield Prediction": "📊 Crop Yield Prediction",
        "Today's Weather": "🌤️ Today's Weather",
        "Fertilizer Recommendation": "🧪 Fertilizer Recommendation",
        "Smart Farming Guidance": "📚 Smart Farming Guidance"
    }

    for key, label in menu_options.items():
        if st.sidebar.button(label, key=key, help=f"Go to {key}"):
            st.session_state['menu'] = key

    selected_menu = st.session_state['menu']

    # Dummy data for charts
    df_yield = pd.DataFrame({
        "Date": ["2025-03-01", "2025-03-02", "2025-03-03", "2025-03-04", "2025-03-05"],
        "Yield": [2, 3, 1, 4, 2]
    })

    # Home page with statistics
    if selected_menu == "Home":
        st.subheader("Statistics")
        col1, col2, col3 = st.columns([1, 1, 1], gap="medium")
        with col1:
            st.markdown('<div class="card"><h3>Yield Over Time</h3></div>', unsafe_allow_html=True)
            fig = px.line(df_yield, x="Date", y="Yield", title="", color_discrete_sequence=["#4caf50"])
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.markdown('<div class="card"><h3>₹ Total Income</h3><p>0</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="card"><h3>🛒 Total Expenses</h3><p>0</p></div>', unsafe_allow_html=True)
        col4, col5 = st.columns([1, 1], gap="medium")
        with col4:
            st.markdown('<div class="card"><h3>🌾 Total Yield</h3><p>0</p></div>', unsafe_allow_html=True)
        with col5:
            st.markdown('<div class="card"><h3>💰 Total Profit</h3><p>0</p></div>', unsafe_allow_html=True)
        st.subheader("Crop Yield Distribution")
        st.markdown("<p style='text-align: center;'>Placeholder for distribution chart (to be implemented with real data)</p>", unsafe_allow_html=True)

    elif selected_menu == "Crop Recommendation":
        st.subheader("🌾 Crop Recommendation System")
        with st.form("crop_form"):
            nitrogen = st.number_input("Nitrogen Level (N)", min_value=0, value=0)
            phosphorus = st.number_input("Phosphorus Level (P)", min_value=0, value=0)
            potassium = st.number_input("Potassium Level (K)", min_value=0, value=0)
            ph = st.number_input("pH Level", min_value=0.0, max_value=14.0, value=7.0)
            rainfall = st.number_input("Rainfall (mm)", min_value=0.0, value=0.0)
            submitted = st.form_submit_button("Recommend Crop")
        if submitted and crop_model:
            if all([nitrogen, phosphorus, potassium, rainfall]):
                features = np.array([[nitrogen, phosphorus, potassium, ph, rainfall]])
                with st.spinner("Analyzing soil data..."):
                    prediction = crop_model.predict(features)
                st.success(f"Recommended Crop: **{prediction[0]}**")
            else:
                st.error("Please fill in all fields.")
        elif submitted and not crop_model:
            st.warning("Crop recommendation model not available yet.")

    elif selected_menu == "Identify Plant Disease":
        st.subheader("🦠 Plant Disease Identification")
        uploaded_file = st.file_uploader("Upload Plant Image", type=["jpg", "png", "jpeg"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            with st.spinner("Analyzing image..."):
                disease = predict_disease(image)
            st.success(f"Detected Disease: **{disease}**")

    elif selected_menu == "Crop Yield Prediction":
        st.subheader("📊 Crop Yield Prediction")
        with st.form("yield_form"):
            area = st.number_input("Field Area (hectares)", min_value=0.0, value=0.0)
            rainfall = st.number_input("Rainfall (mm)", min_value=0.0, value=0.0)
            temperature = st.number_input("Temperature (°C)", min_value=-50.0, max_value=50.0, value=25.0)
            submitted = st.form_submit_button("Predict Yield")
        if submitted:
            if yield_model:
                if all([area, rainfall, temperature]):
                    features = np.array([[area, rainfall, temperature]])
                    with st.spinner("Predicting yield..."):
                        prediction = yield_model.predict(features)
                    st.success(f"Predicted Yield: **{prediction[0]:.2f} tons**")
                else:
                    st.error("Please fill in all fields.")
            else:
                st.warning("Yield prediction model not available yet. Placeholder output: **5.0 tons**")

    elif selected_menu == "Today's Weather":
        st.subheader("🌤️ Weather Forecast")
        with st.form("weather_form"):
            zip_code = st.text_input("Enter ZIP Code", help="e.g., 110001 for Delhi")
            country_code = st.text_input("Enter Country Code", value="IN", help="e.g., IN for India")
            submitted = st.form_submit_button("Get Weather")
        if submitted:
            with st.spinner("Fetching weather data..."):
                weather_data = get_weather(zip_code, country_code)
            if "error" in weather_data:
                st.error(weather_data["error"])
            elif weather_data.get('main'):
                city_name = weather_data.get('name', 'Unknown Location')
                st.markdown(f"<p style='text-align: center;'>**Location**: {city_name}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center;'>**Temperature**: {weather_data['main']['temp']}°C</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center;'>**Weather**: {weather_data['weather'][0]['description'].capitalize()}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='text-align: center;'>**Humidity**: {weather_data['main']['humidity']}%</p>", unsafe_allow_html=True)
            else:
                st.error("Could not retrieve weather data.")

    elif selected_menu == "Fertilizer Recommendation":
        st.subheader("🧪 Fertilizer Recommendation")
        with st.form("fertilizer_form"):
            crop = st.text_input("Enter Crop Name", help="e.g., Rice")
            soil_type = st.text_input("Enter Soil Type", help="e.g., Sandy")
            submitted = st.form_submit_button("Recommend Fertilizer")
        if submitted:
            if fertilizer_model:
                if crop and soil_type:
                    features = np.array([[hash(crop) % 100, hash(soil_type) % 100]])
                    with st.spinner("Analyzing..."):
                        prediction = fertilizer_model.predict(features)
                    st.success(f"Recommended Fertilizer: **{prediction[0]}**")
                else:
                    st.error("Please fill in all fields.")
            else:
                st.warning("Fertilizer recommendation model not available yet. Placeholder output: **NPK 20-20-20**")

    elif selected_menu == "Smart Farming Guidance":
        st.subheader("📚 Smart Farming Guidance")
        with st.form("guidance_form"):
            crop = st.text_input("Enter Crop Name", help="e.g., Wheat")
            country = st.text_input("Enter Country Name", help="e.g., India")
            submitted = st.form_submit_button("Get Smart Farming Info")
        if submitted:
            if crop and country:
                with st.spinner("Fetching guidance..."):
                    guidance = get_smart_farming_info(crop, country)
                st.markdown(f"<div style='text-align: center;'>{guidance}</div>", unsafe_allow_html=True)
                st.image(f"https://source.unsplash.com/600x400/?{crop}", caption=f"{crop.capitalize()}", use_column_width=True)
            else:
                st.error("Please fill in all fields.")

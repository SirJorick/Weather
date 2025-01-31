import json
import requests

def load_weather_config():
    """Load the weather API configuration."""
    # Open the config.json file and load the configuration data
    with open("config.json", "r") as file:
        config_data = json.load(file)

    # Retrieve the API key and weather URL from the config file
    weather_api_key = config_data.get("api_key", "")
    weather_url = config_data.get("url", "http://api.weatherapi.com/v1/current.json")

    # Return the API key and URL for later use
    return weather_api_key, weather_url

def get_rain_message(precip_mm):
    """Returns a precise rain message based on precipitation levels."""
    # Dictionary of precipitation levels and their corresponding messages
    # Predefined sorted keys for the rain levels
    rain_levels = {
        500: "Catastrophic rainfall! Severe flooding, landslides, and extreme danger to life and property.",
        400: "Exceptionally heavy rain! Widespread destruction and life-threatening conditions expected.",
        300: "Super Typhoon-level rain! Extreme flooding, landslides, and major infrastructure damage expected.",
        250: "Extremely heavy rain! Widespread flooding and severe disruptions.",
        200: "Extreme rain detected! Prepare for catastrophic flooding and mudslides.",
        175: "Intense rain! Dangerous flooding is imminent. Evacuate if necessary.",
        150: "Very intense rain! Major flooding likely, stay indoors and avoid travel.",
        125: "Severe rainfall! Rapid water level rise, strong currents possible.",
        100: "Extreme rain detected! Expect severe flooding and hazardous conditions.",
        90: "Very heavy rain! Travel is dangerous, stay alert for rising waters.",
        75: "Torrential rain! Rapidly rising water levels and hazardous conditions.",
        60: "Persistent heavy rain! Flood-prone areas may experience waterlogging.",
        50: "Very heavy rain detected. Stay indoors if possible.",
        40: "Strong downpour detected! Poor visibility and road hazards likely.",
        35: "Heavy downpour detected! Risk of localized flooding.",
        30: "Significant rain! Watch for potential water pooling on roads.",
        25: "Heavy rain detected! Take necessary precautions.",
        20: "Steady rain! Wet conditions may persist for hours.",
        15: "Moderate to heavy rain detected. Visibility may be reduced and roads could be slick.",
        12: "Moderate rainfall! Prolonged exposure may lead to waterlogging.",
        10: "Moderate rain detected. Conditions could worsen.",
        8: "Noticeable rain! Surfaces may become slippery.",
        7: "Steady rain detected. Ground saturation increasing.",
        6: "Intermittent rain showers! Short breaks expected.",
        5: "Light rain detected. Expect slippery roads and possible minor flooding.",
        4: "Scattered light showers! Brief wet spells.",
        3: "Occasional drizzles with short wet periods.",
        2: "Light rain detected. A light umbrella is recommended.",
        1.5: "Misting rain! A fine spray of moisture in the air.",
        1: "Very light rain detected. A very slight drizzle.",
        0.9: "Barely perceptible rain detected. Very light drizzle, almost no impact.",
        0.7: "Thin mist-like drizzle. Barely noticeable.",
        0.5: "Very fine drizzle detected. Minimal accumulation.",
        0.3: "Sparse droplets! Barely wetting the ground.",
        0.2: "Light drizzle detected. Almost no impact.",
        0.1: "Drizzle detected! Fine rain with almost no accumulation.",
        0.05: "Trace moisture detected! A barely perceptible dampness.",
        0: "Not Raining"
    }

    # Sort the keys once (when defining the function)
    rain_keys = sorted(rain_levels.keys(), reverse=True)

    def get_rain_message(precip_mm):
        """Returns a precise rain message based on precipitation levels."""
        # Loop through the sorted rain levels and return the first matching message
        for key in rain_keys:
            if precip_mm >= key:
                return rain_levels[key]

        return "No significant rain detected."


def detect_typhoon_level(precip_mm, wind_kph, region="default", storm_intensity=None):
    """Detect typhoon-level conditions based on precipitation, wind speed, and region-specific thresholds."""

    # Regional thresholds customization based on different weather patterns or local conditions
    if region == "tropical":
        # Tropical regions might experience severe weather with slightly lower wind speeds or precipitation
        if precip_mm >= 300 and wind_kph >= 150:
            return "\n⚠️ Extreme tropical storm conditions detected! Major disruptions expected, prepare for flooding."
        elif precip_mm >= 200 and wind_kph >= 130:
            return "\n⚠️ Severe tropical storm conditions detected. Strong winds and heavy rain expected."
        elif precip_mm >= 100 and wind_kph >= 100:
            return "\n⚠️ Strong tropical storm conditions detected. Expect moderate flooding and gusty winds."

    elif region == "arctic":
        # Arctic regions may have different thresholds due to cold temperatures and less frequent storms
        if precip_mm >= 100 and wind_kph >= 80:
            return "\n⚠️ Severe Arctic storm detected. Snow, high winds, and visibility issues expected."
        elif precip_mm >= 50 and wind_kph >= 60:
            return "\n⚠️ Moderate Arctic storm detected. Snow accumulation and slippery conditions."

    elif region == "coastal":
        # Coastal regions near the ocean may have different storm dynamics due to hurricanes or typhoons
        if precip_mm >= 350 and wind_kph >= 170:
            return "\n⚠️ Catastrophic hurricane-level conditions detected! Life-threatening storm with major flooding."
        elif precip_mm >= 250 and wind_kph >= 150:
            return "\n⚠️ Strong hurricane conditions detected. Prepare for extreme flooding and wind damage."

    # Global default conditions (if no specific region provided or if region doesn't match known categories)
    if precip_mm >= 500 and wind_kph >= 200:
        return "\n⚠️ Catastrophic Typhoon-level conditions detected! Extreme weather, widespread flooding, landslides, and severe damage to infrastructure expected."
    elif precip_mm >= 400 and wind_kph >= 180:
        return "\n⚠️ Exceptional Typhoon-level conditions detected! Extreme danger to life and property due to severe flooding and high winds."
    elif precip_mm >= 300 and wind_kph >= 160:
        return "\n⚠️ Super Typhoon-level conditions detected! Major infrastructure damage expected, with extreme flooding and widespread destruction."
    elif precip_mm >= 250 and wind_kph >= 150:
        return "\n⚠️ Extremely heavy rainfall and winds. Major disruptions, widespread flooding, and possible life-threatening conditions."
    elif precip_mm >= 200 and wind_kph >= 140:
        return "\n⚠️ Severe Typhoon-level conditions detected! Extreme flooding and wind damage expected."
    elif precip_mm >= 150 and wind_kph >= 120:
        return "\n⚠️ Severe tropical storm-level conditions detected! Prepare for heavy rain, strong winds, and possible flooding."
    elif precip_mm >= 120 and wind_kph >= 100:
        return "\n⚠️ Strong storm-level conditions detected! Heavy rain, gusty winds, and localized flooding expected."
    elif precip_mm >= 100 and wind_kph >= 80:
        return "\n⚠️ Tropical storm-level conditions detected. Heavy rainfall and moderate winds expected. Stay alert for flooding."
    elif precip_mm >= 80 and wind_kph >= 70:
        return "\n⚠️ Moderate tropical storm conditions. Heavy rain, gusty winds, and possible localized flooding."
    elif precip_mm >= 50 and wind_kph >= 50:
        return "\n⚠️ Strong wind and moderate rain detected. Risk of localized flooding and road hazards."
    elif precip_mm >= 30 and wind_kph >= 40:
        return "\n⚠️ Moderate storm conditions. Expect rain and gusty winds, localized flooding possible."
    elif precip_mm >= 20 and wind_kph >= 30:
        return "\n⚠️ Strong rainfall with moderate winds. Risk of slippery roads and minor flooding."
    elif precip_mm >= 10 and wind_kph >= 20:
        return "\n⚠️ Moderate rainfall with light winds. Road conditions may be slippery."

    # If no typhoon-level conditions are detected
    return None


def detect_typhoon_status(lat, lng, region="default", forecast_precip_mm=None, forecast_wind_kph=None):
    """Fetch real-time weather data and determine typhoon conditions based on region and forecast data."""
    # Fetch real-time weather data
    weather_data = get_real_time_weather_data(lat, lng)
    if weather_data is None:
        return "Unable to retrieve fresh weather data."

    # Extract precipitation and wind speed from the current weather data
    precip_mm = weather_data.get("current", {}).get("precip_mm", 0)
    wind_kph = weather_data.get("current", {}).get("wind_kph", 0)

    # Add the region to adjust typhoon-level thresholds
    typhoon_message = detect_typhoon_level(precip_mm, wind_kph, region)

    # Optionally, if forecast data is provided, you can also assess future conditions
    if forecast_precip_mm is not None and forecast_wind_kph is not None:
        forecast_typhoon_message = detect_typhoon_level(forecast_precip_mm, forecast_wind_kph, region)
        typhoon_message += f"\nForecast Typhoon-level conditions: {forecast_typhoon_message}"

    return typhoon_message


def get_real_time_weather_data(lat, lng, forecast=False):
    """Fetch real-time weather data using latitude and longitude and validate the freshness of the data."""
    # Load the weather API configuration
    api_key, weather_url = load_weather_config()

    # Construct the API request URL with the given latitude and longitude
    url = f"{weather_url}?key={api_key}&q={lat},{lng}"

    # Send the request to the weather API and retrieve the response
    response = requests.get(url)
    weather_data = response.json()

    # Check if the data returned is fresh (you can add timestamps from the API)
    current_time = weather_data.get("location", {}).get("localtime", "")
    if current_time:
        # Assuming response provides a "localtime" field for validation
        return weather_data
    else:
        return None


def detect_typhoon_status(lat, lng, region="default", forecast_precip_mm=None, forecast_wind_kph=None):
    """Fetch real-time weather data and determine typhoon conditions based on region and forecast data."""
    # Fetch real-time weather data
    weather_data = get_real_time_weather_data(lat, lng)
    if weather_data is None:
        return "Unable to retrieve fresh weather data."

    # Extract precipitation and wind speed from the current weather data
    precip_mm = weather_data.get("current", {}).get("precip_mm", 0)
    wind_kph = weather_data.get("current", {}).get("wind_kph", 0)

    # Add the region to adjust typhoon-level thresholds
    typhoon_message = detect_typhoon_level(precip_mm, wind_kph, region)

    # Optionally, if forecast data is provided, you can also assess future conditions
    if forecast_precip_mm is not None and forecast_wind_kph is not None:
        forecast_typhoon_message = detect_typhoon_level(forecast_precip_mm, forecast_wind_kph, region)
        typhoon_message += f"\nForecast Typhoon-level conditions: {forecast_typhoon_message}"

    return typhoon_message


def get_weather_data(lat, lng):
    """Fetch weather data using latitude and longitude."""
    # Load the weather API configuration
    api_key, weather_url = load_weather_config()

    # Construct the API request URL with the given latitude and longitude
    url = f"{weather_url}?key={api_key}&q={lat},{lng}"

    # Send the request to the weather API and retrieve the response
    response = requests.get(url)
    weather_data = response.json()

    # Extract precipitation and wind speed data from the API response
    precip_mm = weather_data.get("current", {}).get("precip_mm", 0)
    wind_kph = weather_data.get("current", {}).get("wind_kph", 0)

    # Return the extracted weather data
    return precip_mm, wind_kph

def detect_rain(precip_mm, wind_kph, forecast_precip_mm=None, forecast_wind_kph=None):
    """Detect rain and identify potential typhoon-level conditions based on precipitation and wind speed."""
    # Get the rain message based on actual precipitation levels
    actual_rain_message = get_rain_message(precip_mm)

    # If forecasted precipitation exists, return the forecasted rain message
    if forecast_precip_mm is not None:
        forecast_message = get_rain_message(forecast_precip_mm)
    else:
        forecast_message = "No rain forecasted."

    # Combine the actual and forecasted rain messages
    message = f"💧 Rain forecast: {forecast_message}\n🌧 Rain Message: {actual_rain_message}"

    # Detect actual typhoon-level conditions based on actual data
    typhoon_message_actual = detect_typhoon_level(precip_mm, wind_kph)
    if typhoon_message_actual:
        message += typhoon_message_actual  # Add if actual typhoon-level conditions are detected

    # If forecasted typhoon conditions exist, add the forecasted typhoon message
    if forecast_precip_mm is not None and forecast_wind_kph is not None:
        typhoon_message_forecast = detect_typhoon_level(forecast_precip_mm, forecast_wind_kph)
        if typhoon_message_forecast:
            message += typhoon_message_forecast  # Add if forecasted typhoon-level conditions are detected

    # Return the complete rain status message
    return message

def get_rain_status(lat, lng, forecast_precip_mm=None, forecast_wind_kph=None):
    """Fetch weather data and return rain status."""
    # Fetch the current weather data using latitude and longitude
    precip_mm, wind_kph = get_weather_data(lat, lng)

    # Get rain status and potential typhoon conditions based on current data
    rain_status = detect_rain(precip_mm, wind_kph, forecast_precip_mm, forecast_wind_kph)

    # Return the rain status message
    return rain_status

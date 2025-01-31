import requests
from rain_stat import load_weather_config, get_rain_message, detect_typhoon_level
import pytz
import math
from datetime import datetime, timedelta

# Load weather API configuration
weather_api_key, weather_url = load_weather_config()

def wind_direction_to_degrees(wind_dir):
    """Convert wind direction from cardinal to degrees."""
    directions = {
        "N": 0, "NNE": 22.5, "NE": 45, "ENE": 67.5, "E": 90, "ESE": 112.5, "SE": 135, "SSE": 157.5,
        "S": 180, "SSW": 202.5, "SW": 225, "WSW": 247.5, "W": 270, "WNW": 292.5, "NW": 315, "NNW": 337.5
    }
    return directions.get(wind_dir.upper(), "N/A")  # Returns N/A if wind_dir is not valid


def equation_of_time(date):
    """Calculate the equation of time (EoT) for a given date."""
    # Constants for calculation
    day_of_year = date.timetuple().tm_yday  # Day of the year (1 to 365)

    # Calculate omega (angle in degrees)
    omega = (360 / 365) * (day_of_year - 81)

    # Convert omega to radians for the trigonometric functions
    omega_rad = math.radians(omega)

    # Simple approximation formula for the Equation of Time (EoT) in minutes
    EoT = 229.18 * (0.000075 + 0.001868 * math.cos(omega_rad) - 0.032077 * math.sin(omega_rad)
                    - 0.014615 * math.cos(2 * omega_rad) - 0.040849 * math.sin(2 * omega_rad))

    return EoT


def calculate_solar_noon(longitude, date, timezone="UTC"):
    """Calculate solar noon time based on longitude, date, and timezone."""
    # Constants
    standard_meridian = 15  # Every 15° longitude corresponds to 1-hour difference in time
    EoT = equation_of_time(date)  # Equation of time (in minutes)

    # Time zone correction (adjust for local longitude)
    time_offset = (longitude - standard_meridian) * 4  # in minutes

    # Convert the input date to UTC if it's not already
    utc_date = date.astimezone(pytz.utc)

    # Adjust for the timezone
    tz = pytz.timezone(timezone)
    local_time = utc_date.astimezone(tz)

    # Local time of solar noon
    solar_noon_time = 12 * 60 - time_offset + EoT  # in minutes from midnight
    solar_noon_hour = solar_noon_time // 60
    solar_noon_minute = solar_noon_time % 60

    # Convert solar noon time to HH:MM format
    solar_noon = timedelta(hours=solar_noon_hour, minutes=solar_noon_minute)

    # Ensure that the time is within the 24-hour day range
    solar_noon_time_corrected = (datetime.min + solar_noon).time()

    return solar_noon_time_corrected.strftime("%H:%M")


def equation_of_time(date):
    """Calculate the equation of time (in minutes) for a specific date."""
    # Extract day of year (DOY) from the date
    doy = date.timetuple().tm_yday

    # Equation of Time formula (simplified version)
    b = (360 / 365) * (doy - 81)  # Approximation factor
    EoT = 229.18 * (0.000075 + 0.001868 * math.cos(math.radians(b)) - 0.032077 * math.sin(
        math.radians(b)) - 0.014615 * math.cos(2 * math.radians(b)) - 0.040849 * math.sin(2 * math.radians(b)))

    return round(EoT, 2)  # Return equation of time in minutes


def calculate_wind_chill(temp_c, wind_kph, humidity=None, cloud_cover=None, cloud_type=None, cloud_altitude=None,
                         is_night=False, region="default"):
    if wind_kph < 4.8:
        return "Not Applicable (Wind < 4.8 kph)"  # Wind chill is not applicable for very light wind

    # Convert wind speed from kph to mph for wind chill formula
    wind_mph = wind_kph * 0.621371

    if temp_c <= 10:
        # Calculate wind chill using the Fahrenheit-based formula
        temp_f = (temp_c * 9 / 5) + 32  # Convert Celsius to Fahrenheit
        wind_chill_f = 35.74 + 0.6215 * temp_f - 35.75 * (wind_mph ** 0.16) + 0.4275 * temp_f * (wind_mph ** 0.16)

        # Convert back to Celsius for more usable output
        wind_chill_c = (wind_chill_f - 32) * 5 / 9  # Fahrenheit to Celsius conversion
        return f"Feels Like: {round(wind_chill_c, 2)}°C"

    else:
        # Apply cooling effect for temperatures above 10°C
        cooling_effect = temp_c - (0.3 * (wind_kph - 5))  # 0.3°C cooling for each kph above 5 kph

        # Apply stronger cooling effect for wind speeds above 40 kph (very strong winds)
        if wind_kph > 40:
            cooling_effect -= 2  # Additional cooling for very strong winds

        # Apply regional dynamic temperature thresholds
        if region == "tropical":
            cooling_effect -= 0.5  # Tropical regions generally experience less cooling
        elif region == "arctic":
            cooling_effect -= 2  # Arctic regions see more pronounced cooling
        elif region == "desert":
            cooling_effect -= 0.2  # Desert regions experience less cooling due to dry air
        elif region == "mountain":
            cooling_effect -= 1.0  # Mountain regions can experience more cooling, especially with higher altitude winds
        elif region == "temperate":
            cooling_effect -= 0.5  # Temperate regions have average cooling effects

        # Apply edge case handling for extreme temperatures
        if temp_c < -20:  # Extremely cold temperatures
            cooling_effect = max(cooling_effect, -10)  # Allow the cooling effect to reach lower values in arctic regions
        elif temp_c > 40:  # Extremely hot temperatures
            cooling_effect = min(cooling_effect, 40)  # Allow the cooling effect to be capped at higher values in hot environments

        # Apply additional cooling effect at night, with factors for humidity, cloud cover, and cloud type
        if is_night and temp_c > 10:
            # Base cooling at night
            cooling_effect -= min(2, 0.1 * temp_c)  # Apply up to 2°C extra cooling, but scale it based on temperature

            # Adjust for humidity (higher humidity reduces the cooling effect)
            if humidity is not None:
                cooling_effect -= (humidity / 100) * 1.5  # Humidity reduces cooling effect by up to 1.5°C

            # Adjust for cloud cover (clouds tend to trap heat, reducing cooling)
            if cloud_cover is not None:
                if cloud_type == "high":
                    cooling_effect -= (cloud_cover / 100) * 0.5  # High clouds trap heat less, smaller effect
                elif cloud_type == "low":
                    cooling_effect -= (cloud_cover / 100) * 1.5  # Low clouds trap more heat, stronger effect
                elif cloud_type == "mid":
                    cooling_effect -= (cloud_cover / 100) * 1.0  # Mid clouds fall between high and low clouds

                # Further adjust based on cloud altitude and density
                if cloud_altitude is not None:
                    if cloud_altitude > 6000:  # High-altitude clouds (over 6000 meters)
                        cooling_effect -= 1.0  # Less cooling from high clouds
                    elif cloud_altitude < 1000:  # Low-altitude clouds (under 1000 meters)
                        cooling_effect -= 2.0  # Stronger heat trapping effect from low clouds
                    # Consider cloud density (denser clouds trap more heat)
                    if cloud_cover > 70:
                        cooling_effect -= 0.5  # Denser cloud cover traps more heat, reducing cooling

        cooling_effect = max(cooling_effect, 5)  # Ensure cooling effect doesn't go below 5°C (no unrealistic values)

        # Apply different wind speed thresholds for cooling effect
        if wind_kph > 30:
            cooling_effect -= 2  # Strong winds (over 30 kph) cause additional cooling
        elif wind_kph > 20:
            cooling_effect -= 1  # Moderate winds (20-30 kph) cause some additional cooling
        elif wind_kph > 10:
            cooling_effect -= 0.5  # Light winds (10-20 kph) cause a slight additional cooling

        # Add note for strong wind cooling effect if wind speed is greater than 15 kph
        effect_text = " (strong wind cooling effect)" if wind_kph > 15 else ""

        return f"Feels Like: {round(cooling_effect, 2)}°C{effect_text}"



def calculate_hsi(temp_c, humidity):
    """Calculate the Heat Stress Index (HSI) based on temperature and humidity."""

    # Skip calculation if temperature or humidity is too low for significant heat stress
    if temp_c < 26.67 or humidity < 40:  # equivalent to 80°F
        return "HSI N/A (temp. & humidity too low!)"

    # Convert Celsius to Fahrenheit for the formula
    temp_f = (temp_c * 9 / 5) + 32

    # Use the National Weather Service Heat Index Formula
    HI_fahrenheit = (
            -42.379 + 2.04901523 * temp_f + 10.14333127 * humidity - 0.22475541 * temp_f * humidity
            - 6.83783 * 10 ** -3 * temp_f ** 2 - 5.481717 * 10 ** -2 * humidity ** 2
            + 1.22874 * 10 ** -3 * temp_f ** 2 * humidity + 8.5282 * 10 ** -4 * temp_f * humidity ** 2
            - 1.99 * 10 ** -6 * temp_f ** 2 * humidity ** 2
    )

    # Convert the Heat Index to Celsius
    HI_celsius = (HI_fahrenheit - 32) * 5 / 9

    # Categorize the result based on Heat Index
    if HI_fahrenheit > 130:
        return f"HSI: {round(HI_celsius, 2)}°C - Extreme Heat Stress (Dangerous)"
    if HI_fahrenheit > 105:
        return f"HSI: {round(HI_celsius, 2)}°C - High Heat Stress (Take caution)"
    if HI_fahrenheit > 90:
        return f"HSI: {round(HI_celsius, 2)}°C - Moderate Heat Stress (Caution)"
    if HI_fahrenheit > 80:
        return f"HSI: {round(HI_celsius, 2)}°C - Low Heat Stress (Normal)"

    return f"HSI: {round(HI_celsius, 2)}°C - No significant Heat Stress"


def get_weather(lat, lng):
    """Fetch weather data including moon phase."""
    if not weather_api_key or not weather_url:
        return "Weather API key or URL is missing."

    try:
        # Store current time once and reuse it
        today = datetime.now()

        # Make the request to the weather API
        request_url = f"http://api.weatherapi.com/v1/forecast.json?key={weather_api_key}&q={lat},{lng}&days=1&aqi=no&alerts=no"
        response = requests.get(request_url)
        data = response.json()

        if "current" in data and "forecast" in data:
            current = data["current"]
            forecast = data["forecast"]["forecastday"][0]
            astro = forecast["astro"]

            # Extract current weather data
            temp_c = current["temp_c"]
            feels_like_c = current.get("feelslike_c", "N/A")
            condition = current["condition"]["text"]
            humidity = current["humidity"]
            wind_kph = current["wind_kph"]
            wind_dir = current["wind_dir"]
            wind_gust_kph = current.get("gust_kph", "N/A")
            cloud_cover = current.get("cloud", "N/A")
            precip_mm = current.get("precip_mm", 0)
            uv_index = current.get("uv", "N/A")
            visibility_km = current.get("vis_km", "N/A")
            pressure_mb = current.get("pressure_mb", "N/A")

            # Get the wind chill calculation
            wind_chill = calculate_wind_chill(temp_c, wind_kph)

            # Calculate HSI (Heat Stress Index)
            hsi = calculate_hsi(temp_c, humidity)

            # Calculate solar noon if not available from the API
            solar_noon = calculate_solar_noon(lng, today)  # Use the pre-defined function for this

            # Get wind direction in degrees
            wind_dir_degrees = wind_direction_to_degrees(wind_dir)

            # Moon phase
            moon_phase = astro.get("moon_phase", "N/A")

            # Icons based on conditions
            condition_icons = {
                "Clear": "🌞",
                "Partly cloudy": "⛅",
                "Cloudy": "☁️",
                "Rain": "🌧",
                "Snow": "❄️",
                "Wind": "💨",
                "Thunderstorm": "🌩",
                "Fog": "🌫",
                "Drizzle": "🌦",
            }

            condition_icon = condition_icons.get(condition, "🌥")  # Default to "partly cloudy" if unknown

            # Returning formatted weather data with moon phase and icons
            return (
                f"{condition_icon} Weather Condition: {condition}\n"
                f"🌡 Temperature: {temp_c}°C (Feels Like: {feels_like_c}°C)\n"
                f"❄ Wind Chill: {wind_chill}\n"
                f"💨 Wind: {wind_kph} kph (Direction: {wind_dir} - {wind_dir_degrees}°)\n\n"
                f"🌪 Wind Gusts: {wind_gust_kph} kph\n"
                f"💧 Humidity: {humidity}%\n"
                f"☁️ Cloud Cover: {cloud_cover}%\n"
                f"🌧 Precipitation: {precip_mm} mm\n"
                f"🌞 UV Index: {uv_index}\n"
                f"👀 Visibility: {visibility_km} km\n"
                f"🔽 Pressure: {pressure_mb} mb\n"
                f"⏳ Daylight Duration: {astro.get('sunset', 'N/A')} - {astro.get('sunrise', 'N/A')}\n"
                f"🕛 Solar Noon: {solar_noon}\n\n"
                f"🌕 Moon Phase: {moon_phase}\n\n"
                f"{hsi}\n\n"
                f"🌅 Sunrise: {astro.get('sunrise', 'N/A')}\n"
                f"🌇 Sunset: {astro.get('sunset', 'N/A')}\n\n"
                f"🌦 Condition Today: {condition}\n"
                f"🌧 Rain Message: {get_rain_message(precip_mm)}\n\n"
                f"🌪 Typhoon Level: {detect_typhoon_level(precip_mm, wind_kph)}\n"
            )
        else:
            return "Weather data not available."

    except Exception as e:
        return f"Error fetching weather data: {e}"




import tkinter as tk
from tkinter import ttk
import requests
from datetime import datetime
import pytz
from geopy.distance import geodesic

# Updated configuration without address and OpenCage API key
config = {
    "api_key": "3d64780a9a2b44cbb4162710242812",
    "url": "http://api.weatherapi.com/v1/current.json"
}

# Function to calculate distance between two lat-lng pairs (in km)
def calculate_distance(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

# Function to get coordinates dynamically using OpenCage API for a given timezone
def get_coordinates_from_timezone(timezone):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={timezone}&key=9bb391df378541a283fe99b321a33929"
    response = requests.get(url)
    data = response.json()
    if data.get("results"):
        location = data["results"][0]
        lat = location["geometry"]["lat"]
        lon = location["geometry"]["lng"]
        return lat, lon
    else:
        raise Exception(f"Unable to fetch coordinates for timezone: {timezone}")

# Function to get weather data from WeatherAPI
def get_weather_data(lat, lon, api_key):
    url = f"{config['url']}?key={api_key}&q={lat},{lon}"
    response = requests.get(url)
    data = response.json()
    return data

# Function to get typhoons within a specified radius
def get_typhoons_within_radius(lat, lon, radius_km=500):
    url = f"{config['url']}?key={config['api_key']}&q={lat},{lon}&alerts=yes"
    response = requests.get(url)
    data = response.json()
    nearby_typhoons = []
    for alert in data.get('alerts', []):
        typhoon_lat = alert.get('location', {}).get('lat', None)
        typhoon_lon = alert.get('location', {}).get('lon', None)
        if typhoon_lat and typhoon_lon:
            distance = calculate_distance(lat, lon, typhoon_lat, typhoon_lon)
            if distance <= radius_km:
                nearby_typhoons.append({
                    'headline': alert.get('headline', 'No Headline'),
                    'description': alert.get('description', 'No Description'),
                    'distance': distance
                })
    return nearby_typhoons

# Function to extract weather data
def extract_weather_data(weather_data):
    location = weather_data.get('location', {})
    current = weather_data.get('current', {})
    city = location.get('name', 'Unknown')
    region = location.get('region', 'Unknown')
    country = location.get('country', 'Unknown')
    lat = location.get('lat', 0)
    lon = location.get('lon', 0)
    temperature = current.get('temp_c', 'N/A')
    wind_speed = current.get('wind_kph', 'N/A')
    humidity = current.get('humidity', 'N/A')
    pressure = current.get('pressure_mb', 'N/A')
    timezone = location.get('tz_id', 'Unknown Timezone')
    local_time = location.get('localtime', 'Unknown Time')
    timezone_info = pytz.timezone(timezone) if timezone != 'Unknown Timezone' else pytz.UTC
    current_time = datetime.strptime(local_time, "%Y-%m-%d %H:%M") if local_time != 'Unknown Time' else datetime.utcnow()
    current_time = current_time.astimezone(timezone_info).strftime('%Y-%m-%d %H:%M:%S')

    return {
        'location': f"{city}, {region}, {country}",
        'lat': lat,
        'lon': lon,
        'temperature': temperature,
        'wind_speed': wind_speed,
        'humidity': humidity,
        'pressure': pressure,
        'timezone': timezone,
        'current_time': current_time
    }

# Function to format weather data
def format_weather_results(weather_data, radius_km=500):
    weather_info = extract_weather_data(weather_data)
    lat, lon = weather_info['lat'], weather_info['lon']
    nearby_typhoons = get_typhoons_within_radius(lat, lon, radius_km)

    formatted_result = f"Location: {weather_info['location']}\n"
    formatted_result += f"Local Time: {weather_info['current_time']}\n"
    formatted_result += f"Timezone: {weather_info['timezone']}\n\n"
    formatted_result += f"Temperature: {weather_info['temperature']} °C\n"
    formatted_result += f"Wind Speed: {weather_info['wind_speed']} km/h\n"
    formatted_result += f"Humidity: {weather_info['humidity']}%\n"
    formatted_result += f"Pressure: {weather_info['pressure']} hPa\n\n"

    if nearby_typhoons:
        formatted_result += f"Nearby Typhoons (within {radius_km} km radius):\n"
        for typhoon in nearby_typhoons:
            formatted_result += f"Headline: {typhoon['headline']}\n"
            formatted_result += f"Description: {typhoon['description']}\n"
            formatted_result += f"Distance: {typhoon['distance']:.2f} km\n\n"
    else:
        formatted_result += f"No typhoons found within {radius_km} km radius.\n"

    return formatted_result

# Function to refresh weather data and update the textbox
def refresh_weather_data(textbox, radius_km, timezone_combobox):
    try:
        timezone = timezone_combobox.get()  # Get the selected timezone
        lat, lon = get_coordinates_from_timezone(timezone)
        weather_data = get_weather_data(lat, lon, config['api_key'])
        formatted_result = format_weather_results(weather_data, radius_km)

        textbox.delete(1.0, tk.END)
        textbox.insert(tk.END, formatted_result)

        # Schedule the next refresh after 10 seconds
        textbox.after(10000, refresh_weather_data, textbox, radius_km, timezone_combobox)

    except Exception as e:
        textbox.insert(tk.END, f"Error occurred: {e}\n")

# Function to create the GUI
def create_gui():
    window = tk.Tk()
    window.title("Typhoon Detection Results")

    textbox = tk.Text(window, width=100, height=20)
    textbox.pack(pady=20)

    radius_label = tk.Label(window, text="Select Typhoon Detection Radius (km):")
    radius_label.pack()

    radius_combobox = ttk.Combobox(window, values=[300, 500, 1000, 1500, 2000], state="readonly")
    radius_combobox.set(500)
    radius_combobox.pack(pady=10)

    timezone_label = tk.Label(window, text="Select Timezone:")
    timezone_label.pack()

    all_timezones = pytz.all_timezones
    timezone_combobox = ttk.Combobox(window, values=all_timezones, state="readonly")
    timezone_combobox.set("Asia/Manila")  # Default timezone
    timezone_combobox.pack(pady=10)

    # Start auto-refresh when button is clicked
    button = tk.Button(window, text="Start Continuous Detection", command=lambda: refresh_weather_data(
        textbox, int(radius_combobox.get()), timezone_combobox))
    button.pack()

    window.mainloop()

# Run the GUI
create_gui()

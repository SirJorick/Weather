import tkinter as tk
from tkinter import ttk
import requests
import time
from datetime import datetime
from geopy.distance import geodesic
import pytz
from threading import Thread

# Configuration without address and OpenCage API key
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

    # Check if the response is successful
    if response.status_code != 200:
        raise Exception(f"Error: Unable to fetch weather data (status code {response.status_code})")

    data = response.json()
    return data


# Function to get typhoons within a specified radius and classify Typhoon Level
def get_typhoons_within_radius(lat, lon, radius_km=500):
    url = f"{config['url']}?key={config['api_key']}&q={lat},{lon}&alerts=yes"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Error: Unable to fetch typhoon data (status code {response.status_code})")

    data = response.json()
    nearby_typhoons = []
    if 'alerts' in data:
        for alert in data['alerts']:
            typhoon_lat = alert.get('location', {}).get('lat', None)
            typhoon_lon = alert.get('location', {}).get('lon', None)
            if typhoon_lat and typhoon_lon:
                distance = calculate_distance(lat, lon, typhoon_lat, typhoon_lon)
                if distance <= radius_km:
                    typhoon_info = {
                        'headline': alert.get('headline', 'No Headline'),
                        'description': alert.get('description', 'No Description'),
                        'distance': distance
                    }
                    # Classify typhoon level based on distance or severity (simple categorization)
                    if distance < 100:
                        typhoon_info['level'] = 'Severe Typhoon (Very Close)'
                    elif distance < 300:
                        typhoon_info['level'] = 'Moderate Typhoon (Close)'
                    else:
                        typhoon_info['level'] = 'Weak Typhoon (Far)'
                    nearby_typhoons.append(typhoon_info)
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
    current_time = datetime.strptime(local_time,
                                     "%Y-%m-%d %H:%M") if local_time != 'Unknown Time' else datetime.utcnow()
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
            formatted_result += f"Distance: {typhoon['distance']:.2f} km\n"
            formatted_result += f"Typhoon Level: {typhoon['level']}\n\n"
    else:
        formatted_result += f"No typhoons found within {radius_km} km radius.\n"

    return formatted_result


# Function to wrap the text output word by word
def wrap_text(text, max_length=40):
    words = text.split(' ')
    wrapped_text = ""
    line = ""

    for word in words:
        if len(line + word) + 1 <= max_length:
            line += (" " + word) if line else word
        else:
            wrapped_text += line + "\n"
            line = word
    wrapped_text += line  # Add any remaining words as the last line
    return wrapped_text


# Function to refresh weather data and update the textbox
def refresh_weather_data(textbox, timezone_combobox, radius_list, index, progress_bar):
    try:
        # Get the selected timezone
        timezone = timezone_combobox.get()
        # Get coordinates for the selected timezone
        lat, lon = get_coordinates_from_timezone(timezone)

        # Get weather data
        weather_data = get_weather_data(lat, lon, config['api_key'])

        # Format and wrap results
        formatted_result = format_weather_results(weather_data, radius_list[index])
        wrapped_result = wrap_text(formatted_result)

        # Update the textbox with the wrapped results
        textbox.delete(1.0, tk.END)
        textbox.insert(tk.END, wrapped_result)

    except Exception as e:
        textbox.insert(tk.END, f"Error occurred: {e}\n")


# Global control variable for fetch state
fetch_running = False

# Function to update the progress bar based on time
def update_progress_bar(progress_bar, cycle_time=30):
    def fill_progress_bar():
        if fetch_running:  # Only run if fetching is active
            if progress_bar['value'] < 100:
                progress_bar['value'] += 100 / cycle_time  # Progress bar fills over cycle_time seconds
                progress_bar.after(1000, fill_progress_bar)  # Update every second
            else:
                progress_bar['value'] = 0  # Reset after full cycle and start again
                fill_progress_bar()  # Restart immediately

    progress_bar['value'] = 0  # Reset at the start of each cycle
    fill_progress_bar()  # Start progress update


# Function to cycle through radius values every cycle_time seconds
def cycle_radius(textbox, timezone_combobox, radius_list, index, progress_bar, cycle_time=30):
    if not fetch_running:  # Stop cycling if fetching is disabled
        return

    refresh_weather_data(textbox, timezone_combobox, radius_list, index, progress_bar)

    # Schedule the next cycle
    next_index = (index + 1) % len(radius_list)
    progress_bar.after(cycle_time * 1000, cycle_radius, textbox, timezone_combobox, radius_list, next_index, progress_bar, cycle_time)


# Function to toggle start/stop for fetching
def toggle_fetch(textbox, window, progress_bar, timezone_combobox, radius_list, button):
    global fetch_running  # Use global variable to control execution

    if button['text'] == 'Start':
        fetch_running = True
        button.config(text='Stop', bg="red", fg="white", font=("Arial", 10))  # Set font size to 10
        timezone_combobox.config(state='disabled')  # Disable the combobox
        update_progress_bar(progress_bar)  # Start the progress bar loop
        cycle_radius(textbox, timezone_combobox, radius_list, 0, progress_bar)  # Start data fetching cycle
    else:
        fetch_running = False
        button.config(text='Start', bg="green", fg="white", font=("Arial", 10))  # Set font size to 10
        timezone_combobox.config(state='normal')  # Enable the combobox
        progress_bar['value'] = 0  # Reset progress bar



# Function to create the GUI
def create_gui():
    window = tk.Tk()
    window.title("Typhoon Detection Results")
    window.geometry("500x640")
    window.config(bg="#f0f0f0")  # Set background color for window

    # Create frames for better organization
    main_frame = tk.Frame(window, bg="#f0f0f0")
    main_frame.pack(padx=20, pady=20)

    # Textbox for displaying weather data
    textbox = tk.Text(main_frame, width=60, height=30, bg="black", fg="white", font=("Courier", 10), wrap="word")
    textbox.grid(row=0, column=0, columnspan=2, pady=20)

    # Frame for timezone selection
    timezone_frame = tk.Frame(main_frame, bg="#f0f0f0")
    timezone_frame.grid(row=1, column=0, pady=10, sticky="w")
    timezone_label = tk.Label(timezone_frame, text="Select Timezone:", bg="#f0f0f0", font=("Arial", 10))
    timezone_label.pack(side="left")
    all_timezones = pytz.all_timezones
    timezone_combobox = ttk.Combobox(timezone_frame, values=all_timezones, state="readonly", font=("Arial", 10))
    timezone_combobox.set("Asia/Manila")  # Default timezone
    timezone_combobox.pack(side="left", padx=10)

    # Button for starting/stopping weather data fetching
    fetch_button = tk.Button(main_frame, text="Start", command=lambda: toggle_fetch(textbox, window, progress_bar, timezone_combobox, [500, 1000, 1500, 2000], fetch_button), bg="green", fg="white", font=("Arial", 10))
    fetch_button.grid(row=1, column=1, padx=10)

    # Progress bar for fetching status
    progress_bar = ttk.Progressbar(main_frame, length=300, mode='determinate')
    progress_bar.grid(row=2, column=0, columnspan=2, pady=10)

    window.mainloop()


# Run the GUI
create_gui()

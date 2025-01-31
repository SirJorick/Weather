import json
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
import time
import subprocess
from datetime import datetime
import webbrowser
from urllib.parse import quote_plus
from fetch_weather import get_weather

# Load configuration from config.json
try:
    with open("config.json", "r") as file:
        config_data = json.load(file)  # Parse the JSON configuration file
except (FileNotFoundError, json.JSONDecodeError):
    config_data = {}  # If file doesn't exist or there's an error, use empty dictionary

# Extract data from configuration
address = config_data.get("address")  # Default address if available
open_cage_api_key = config_data.get("open_cage_api_key", "")  # OpenCage API key for geolocation
open_cage_url = config_data.get("open_cage_url", "")  # OpenCage URL for geolocation API
weather_api_key = config_data.get("api_key", "")  # Weather API key for weather information
weather_url = config_data.get("url", "")  # Weather API URL

def get_coordinates(address):
    """Retrieve latitude and longitude based on a given address using OpenCage API."""
    if not address:
        return None, None, None
    try:
        # Create the request URL for OpenCage API
        request_url = f"{open_cage_url}?q={quote_plus(address)}&key={open_cage_api_key}"
        response = requests.get(request_url, timeout=5)  # Make the API request
        response.raise_for_status()  # Raise error if request failed
        data = response.json()  # Parse the JSON response
        if data.get('results'):  # Check if results are found
            first_result = data['results'][0]
            return first_result.get('formatted', 'Unknown Address'), first_result['geometry']['lat'], \
            first_result['geometry']['lng']  # Return formatted address, lat, and long
    except requests.RequestException as e:
        print(f"Error getting coordinates: {e}")  # Print error if the request fails
    return None, None, None

def load_addresses():
    """Load all saved addresses from the address.log file."""
    try:
        with open("address.log", "r", encoding="utf-8-sig") as file:
            return list(set(line.strip().upper() for line in file if line.strip()))  # Read and clean address
    except UnicodeDecodeError:
        # If there's an error reading with utf-8, try another encoding
        with open("address.log", "r", encoding="ISO-8859-1") as file:
            return list(set(line.strip().upper() for line in file if line.strip()))

def load_temp_address():
    """Load the most recent temporary address from temp.log."""
    try:
        with open("temp.log", "r", encoding="utf-8") as file:
            return file.readline().strip()  # Read the address from the first line of temp.log
    except FileNotFoundError:
        return ""  # Return an empty string if temp.log is not found

def save_address(address):
    """Save a new address to address.log after validating it."""
    cleaned_address = address.strip().upper()  # Clean and convert address to uppercase

    if not cleaned_address:
        print("Address is empty or invalid.")  # If address is empty, don't save it
        return

    # Convert the address to coordinates and get the formatted address
    formatted_address, lat, lng = get_coordinates(cleaned_address)

    if not formatted_address or not lat or not lng:
        print("Invalid location. Coordinates not found.")  # If coordinates are invalid, don't save the address
        return

    formatted_address_upper = formatted_address.upper()  # Ensure it's in uppercase for consistency

    # Load existing addresses from address.log
    addresses = load_addresses()

    # Check if the address already exists
    if formatted_address_upper in addresses:
        print("Address already exists. Duplicate addresses are not allowed.")  # Prevent duplicate addresses
        return

    # Insert the new address at the top of the list
    addresses.insert(0, formatted_address_upper)

    try:
        # Save the list of addresses back to address.log
        with open("address.log", "w", encoding="utf-8") as file:
            file.write("\n".join(addresses) + "\n")
        print(f"Address '{formatted_address_upper}' saved.")  # Confirm the save

        # Update the combobox to reflect the new address
        update_combobox()

        # Save the formatted address to temp.log
        save_temp_address(formatted_address_upper)

    except Exception as e:
        print(f"Error saving address: {e}")  # Print any error that occurs while saving

def save_temp_address(address):
    """Save the temporary address to temp.log."""
    with open("temp.log", "w", encoding="utf-8") as file:
        file.write(address + "\n")

def update_combobox():
    """Update the combobox values with the latest list of addresses."""
    combobox["values"] = load_addresses()

def delete_address(address):
    """Delete the selected address from address.log."""
    addresses = load_addresses()  # Load the current addresses
    if address in addresses:
        addresses.remove(address)  # Remove the selected address
        try:
            # Save the updated list of addresses back to address.log
            with open("address.log", "w", encoding="utf-8") as file:
                file.write("\n".join(addresses) + "\n")
            print(f"Address '{address}' deleted.")  # Confirm the deletion
            update_combobox()  # Update the combobox after deletion
        except Exception as e:
            print(f"Error deleting address: {e}")  # Print any errors that occur while deleting
    else:
        print(f"Address '{address}' not found.")  # Print if the address wasn't found

def update_textbox():
    """Update the text output with the selected address' coordinates and weather information."""
    selected_address = combobox.get().strip()  # Get the address from the combobox
    formatted_address, lat, lng = get_coordinates(selected_address)  # Get coordinates of the address
    text_output.config(state=tk.NORMAL)  # Enable editing of the text widget
    text_output.delete(1.0, tk.END)  # Clear the current content

    if formatted_address:
        # If valid address, display coordinates and add a hyperlink to the address
        text_output.insert(tk.END, f"Coordinates:\nLat: {lat}, Lon: {lng}\n\n")
        add_hyperlink(formatted_address)  # Add a hyperlink to Google Maps

        text_output.insert(tk.END, "\nWEATHER:\n\n")  # Show weather data
        weather_data = get_weather(lat, lng)  # Fetch weather data for the coordinates
        if weather_data:
            text_output.insert(tk.END, weather_data)  # Insert weather data
        else:
            text_output.insert(tk.END, "\nError fetching weather data.\n")  # If there's an error, show message

        save_temp_address(formatted_address)  # Save the address to temp.log for future use
    else:
        text_output.insert(tk.END, "\nLocation not found!\n")  # If no valid address, show error message

    text_output.config(state=tk.DISABLED)  # Disable editing again

def add_hyperlink(text):
    """Add a hyperlink to the address, making it clickable."""
    start_idx = text_output.index(tk.INSERT)  # Get the current position in the text widget
    encoded_text = quote_plus(text)  # Encode the address for use in a URL
    text_output.insert(tk.END, text + "\n")  # Insert the address text
    end_idx = text_output.index(tk.INSERT)  # Get the new position after insertion
    tag_name = f"hyperlink_{int(time.time())}"  # Create a unique tag for the hyperlink
    text_output.tag_add(tag_name, start_idx, end_idx)  # Apply the tag to the inserted text
    text_output.tag_config(tag_name, foreground="blue", underline=True)  # Style the hyperlink
    text_output.tag_bind(tag_name, "<Button-1>", lambda e: open_link(encoded_text))  # Open link on click
    text_output.tag_bind(tag_name, "<Enter>", lambda e: text_output.config(cursor="hand2"))  # Change cursor to hand on hover
    text_output.tag_bind(tag_name, "<Leave>", lambda e: text_output.config(cursor=""))  # Revert cursor on leave

def open_link(url):
    """Open the hyperlink in a web browser."""
    webbrowser.open(f"https://www.google.com/maps?q={url}&t=k")

def fetch_weather_periodically():
    """Fetch weather data periodically while the app is running."""
    if running:
        root.after(30000, fetch_weather_periodically)  # Re-run every 30 seconds
        root.after(0, update_textbox)  # Update the text box immediately

def toggle_run():
    """Toggle the state of the app between running and stopped."""
    global running
    running = not running
    run_button.config(text="Stop" if running else "Run")  # Change the button text based on state
    combobox.config(state="disabled" if running else "normal")  # Disable the combobox while running

    selected_address = combobox.get().strip()  # Get the selected address

    if running:
        save_address(selected_address)  # Save the address when the app starts
        fetch_weather_periodically()  # Start periodic weather updates

def update_time():
    """Update the time label every second."""
    if time_label.winfo_exists():  # Check if the time label still exists
        time_label.config(text=datetime.now().strftime("%I:%M:%S %p %b %d, %Y"))  # Update with current time
        root.after(1000, update_time)  # Update the time every second

def run_detect_typhoon():
    """Run the external detect_typhoon.py script."""
    python_executable = r"C:\Users\user\PycharmProjects\Weather\.venv\Scripts\python.exe"
    script_path = r"C:\Users\user\PycharmProjects\Weather\detect_typhoon.py"
    subprocess.Popen([python_executable, script_path])  # Run the script using subprocess

    # Function to save the address whenever the combobox value changes
def on_combobox_change(event):
    selected_address = combobox.get().strip()
    if selected_address:
        print(f"New Address Selected: {selected_address}")  # Debugging message
        save_address(selected_address)  # Save the address
        update_combobox()  # Update combobox with new list of addresses

# Create main application window
root = tk.Tk()
root.title("Weather Info")
root.geometry("600x800")  # Set window size
root.configure(bg="#f4f4f9")  # Set a light background color for the main window

running = False  # App is not running by default
addresses = load_addresses()  # Load saved addresses
default_location = load_temp_address() or config_data.get("address")  # Load the default location

# Combobox to select addresses
combobox = ttk.Combobox(root, values=addresses, state="normal", width=80)
combobox.set(default_location)  # Set the default location in the combobox
combobox.grid(row=0, column=0, columnspan=2, padx=20, pady=10)

# Textbox to display coordinates and weather info
text_output = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=75, height=40, state=tk.DISABLED, font=("Arial", 10), bg="#ffffff", fg="#333333", bd=2)
text_output.grid(row=1, column=0, columnspan=2, padx=20, pady=10)


# Footer frame containing control buttons
footer_frame = tk.Frame(root, bg="#f4f4f9")
footer_frame.grid(row=2, column=0, columnspan=2, pady=(0, 20), sticky="ew")

# Button to toggle app run state
run_button = tk.Button(footer_frame, text="Run", command=toggle_run, bg="#3498db", fg="white", font=("Arial", 10), relief="raised", bd=2)
run_button.grid(row=0, column=0, padx=10, pady=10, sticky="w")

# Button to run typhoon detection script
btn = tk.Button(footer_frame, text="Run Detect Typhoon", command=run_detect_typhoon, bg="#a2c4c9", fg="black", font=("Arial", 10), relief="raised", bd=2)
btn.grid(row=0, column=2, padx=10, pady=10, sticky="e")

# Label to display current time
time_label = tk.Label(footer_frame, font=("Arial", 10), bg="#f4f4f9", fg="#555555")
time_label.grid(row=0, column=1, padx=10, pady=20, sticky="e")

# Button to delete the selected address
delete_button = tk.Button(footer_frame, text="Delete Address", command=lambda: delete_address(combobox.get().strip()), bg="#e74c3c", fg="white", font=("Arial", 10), relief="raised", bd=2)
delete_button.grid(row=0, column=3, padx=10, pady=10, sticky="e")

# Start time update loop
update_time()

# Bind combobox selection change event
combobox.bind("<<ComboboxSelected>>", on_combobox_change)

root.mainloop()  # Start the main application loop

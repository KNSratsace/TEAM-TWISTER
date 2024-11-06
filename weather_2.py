import requests
import urllib.parse
import tkinter as tk
from tkinter import messagebox
import polyline  # Make sure to install with `pip install polyline`- helps with checking cords- for weather

# API Keys and URLs
route_url = "https://graphhopper.com/api/1/route?"
key = "1f2f13b4-8c78-4d72-b9e9-1963e7fdef90"
weather_url = "https://api.openweathermap.org/data/2.5/weather?"
weather_key = "90104da57ecd8130626e78f0b9e5a96e"
geocode_url = "https://graphhopper.com/api/1/geocode?"

# Weather Function
def get_weather(lat, lng, weather_key):
    try:
        url = weather_url + urllib.parse.urlencode({
            "lat": lat,
            "lon": lng,
            "appid": weather_key,
            "units": "imperial",
            "exclude": "minutely,hourly"
        })

        response = requests.get(url)
        if response.status_code == 200:
            weather_data = response.json()
            current_temp = weather_data['main']['temp']
            current_description = weather_data['weather'][0]['description']
            return current_temp, current_description
        else:
            return None, None
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return None, None

# Reverse Geocoding Function to get city and state names
def reverse_geocode(lat, lng):
    try:
        url = geocode_url + urllib.parse.urlencode({"point": f"{lat},{lng}", "key": key})
        response = requests.get(url)
        json_data = response.json()
        if response.status_code == 200 and len(json_data["hits"]) != 0:
            name = json_data["hits"][0]["name"]
            state = json_data["hits"][0].get("state", "")
            return name, state
        return None, None
    except Exception as e:
        print(f"Error in reverse geocoding: {e}")
        return None, None

# Geocoding Function
def geocoding(location, key):
    try:
        url = geocode_url + urllib.parse.urlencode({"q": location, "limit": "1", "key": key})
        response = requests.get(url)
        json_data = response.json()

        if response.status_code == 200 and len(json_data["hits"]) != 0:
            lat = json_data["hits"][0]["point"]["lat"]
            lng = json_data["hits"][0]["point"]["lng"]
            name = json_data["hits"][0]["name"]
            return response.status_code, lat, lng, name
        else:
            return response.status_code, None, None, location
    except Exception as e:
        print(f"Error in geocoding: {e}")
        return None, None, None, location

# Route Function to get directions - set to car only
def get_directions(orig, dest, vehicle="car"):
    op = "&point=" + str(orig[1]) + "%2C" + str(orig[2])
    dp = "&point=" + str(dest[1]) + "%2C" + str(dest[2])
    paths_url = route_url + urllib.parse.urlencode({"key": key, "vehicle": vehicle}) + op + dp
    response = requests.get(paths_url)

    try:
        paths_data = response.json()
        if "paths" in paths_data and len(paths_data["paths"]) > 0:
            directions = []
            # Decode the points from the encoded polyline
            encoded_points = paths_data["paths"][0]["points"]
            points = polyline.decode(encoded_points)
            
            # Parse instructions for turn-by-turn directions
            for each in paths_data["paths"][0]["instructions"]:
                path = each["text"]
                distance = each["distance"]
                directions.append(f"{path} ({distance/1000:.1f} km)")

            return directions, paths_data["paths"][0]["distance"], paths_data["paths"][0]["time"], points
        else:
            print(f"Unexpected API response: {paths_data}")
            return None, None, None, None
    except ValueError as ve:
        print(f"Error parsing JSON response: {ve}")
        print(f"Response content: {response.text}")
        return None, None, None, None
    except Exception as e:
        print(f"Error in getting directions: {e}")
        print(f"Response content: {response.text}")
        return None, None, None, None

# Function to display weather and directions
def show_info():
    loc1 = entry_start.get()
    loc2 = entry_dest.get()

    # Disable the button to prevent multiple clicks during processing
    button_info.config(state=tk.DISABLED)
    result_text.set("Processing...")

    # Get Geocoding data for start and destination
    orig = geocoding(loc1, key)
    dest = geocoding(loc2, key)

    if dest[0] == 200:
        # Get Weather at destination
        temp, description = get_weather(dest[1], dest[2], weather_key)
        if temp is not None and description is not None:
            result_text.set(f"Weather at {dest[3]}: {temp}°F, {description}")
        else:
            result_text.set("No weather info available.")
        
        # Get Directions and Points Along the Route
        directions, distance, time, points = get_directions(orig, dest, "car")
        if directions and points:
            miles = distance / 1000 / 1.61
            time_in_hours = time / 1000 / 60 / 60
            directions_output = f"Distance: {miles:.1f} miles, Time: {time_in_hours:.1f} hours\n" + "\n".join(directions)
            text_directions.delete(1.0, tk.END)  # Clear previous content
            text_directions.insert(tk.END, directions_output)

            # Monitor Weather Along the Route
            previous_city_state = None
            weather_updates = []
            for idx, point in enumerate(points[::10]):  # Check every 10th point - unable to use API for city/state change
                lng, lat = point[1], point[0]
                city, state = reverse_geocode(lat, lng)
                if city and state and (city, state) != previous_city_state:
                    temp, description = get_weather(lat, lng, weather_key)
                    if temp and description:
                        weather_updates.append(f"Weather in {city}, {state}: {temp}°F, {description}")
                    previous_city_state = (city, state)

            # Display Weather Updates Along the Route
            if weather_updates:
                route_weather.set("\n".join(weather_updates))
            else:
                route_weather.set("No weather updates found along the route.")
        else:
            text_directions.delete(1.0, tk.END)
            text_directions.insert(tk.END, "Could not get directions.")
    else:
        result_text.set("Error in getting destination info.")

    # Re-enable the button after processing
    button_info.config(state=tk.NORMAL)

# Tkinter - Gui Maker
root = tk.Tk()
root.title("Weather and Directions Finder")

# boxes for start and destination - Do Not Exceed Width of 50. All Citys& States will fit in that width.
label_start = tk.Label(root, text="Starting Location:")
label_start.grid(row=0, column=0)

entry_start = tk.Entry(root, width=30)
entry_start.grid(row=0, column=1)

label_dest = tk.Label(root, text="Destination:")
label_dest.grid(row=1, column=0)

entry_dest = tk.Entry(root, width=30)
entry_dest.grid(row=1, column=1)

# Button = weather and directions
button_info = tk.Button(root, text="Get Info", command=show_info)
button_info.grid(row=2, column=1)

# Display the weather result
result_text = tk.StringVar()
label_result = tk.Label(root, textvariable=result_text, wraplength=300)
label_result.grid(row=3, column=0, columnspan=2)

# Text widget with scrollbar for directions
frame_directions = tk.Frame(root)
frame_directions.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

text_directions = tk.Text(frame_directions, wrap=tk.WORD, height=15, width=50)
scrollbar = tk.Scrollbar(frame_directions, command=text_directions.yview)
text_directions.configure(yscrollcommand=scrollbar.set)

text_directions.grid(row=0, column=0)
scrollbar.grid(row=0, column=1, sticky='ns')

# Text widget to display route weather updates
route_weather = tk.StringVar()
label_route_weather = tk.Label(root, textvariable=route_weather, wraplength=400, fg="blue")
label_route_weather.grid(row=5, column=0, columnspan=2)

# Start the GUI loop
root.mainloop()

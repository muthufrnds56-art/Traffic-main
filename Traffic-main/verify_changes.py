import requests
import json
import sys

API_URL = "http://localhost:8000"

def test_sensor_list():
    print("Testing /api/sensors/list...")
    try:
        response = requests.get(f"{API_URL}/api/sensors/list")
        if response.status_code == 200:
            data = response.json()
            sensors = data.get("sensors", [])
            print(f"Found {len(sensors)} sensors.")
            
            bangalore_locations = [
                "MG Road", "Hosur Road", "Indiranagar 100ft Road", "Outer Ring Road",
                "Jayanagar 4th Block", "Bellary Road", "Koramangala 80ft Road", "Bannerghatta Road"
            ]
            
            found_locations = [s["location"] for s in sensors]
            print("Locations found:", found_locations)
            
            if any(loc in found_locations for loc in bangalore_locations):
                print("SUCCESS: Bangalore locations found in sensor list.")
            else:
                print("FAILURE: Bangalore locations NOT found in sensor list.")
        else:
            print(f"FAILURE: API returned status code {response.status_code}")
    except Exception as e:
        print(f"FAILURE: Error connecting to API: {e}")

def test_route_optimization():
    print("\nTesting /api/routes/optimize...")
    try:
        payload = {
            "start_location": "MG Road",
            "end_location": "Indiranagar 100ft Road",
            "preferred_route_type": "fastest"
        }
        response = requests.post(f"{API_URL}/api/routes/optimize", json=payload)
        if response.status_code == 200:
            data = response.json()
            print("Route optimization successful.")
            print("Recommended Route:", json.dumps(data.get("recommended_route"), indent=2))
            
            # Check if waypoints are from Bangalore pool
            route = data.get("recommended_route", {})
            path = route.get("path", [])
            print("Path:", path)
            
            if "MG Road" in path and "Indiranagar 100ft Road" in path:
                print("SUCCESS: Route contains start and end locations.")
            else:
                print("FAILURE: Route missing start/end locations.")
        else:
            print(f"FAILURE: API returned status code {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"FAILURE: Error connecting to API: {e}")

if __name__ == "__main__":
    test_sensor_list()
    test_route_optimization()

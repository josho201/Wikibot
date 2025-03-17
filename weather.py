
import requests
def get_weather(city_name, api_key):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city_name,
        'appid': api_key,
        'units': 'metric'  # Use 'imperial' for Fahrenheit
    }
    
    response = requests.get(base_url, params=params)
    data = response.json()
    
    if response.status_code == 200:
        return data
    else:
        return None
def main():
    api_key = "your_api_key_here"  # Replace with your actual API key
    city_name = input("Enter the name of the city: ")
    weather_data = get_weather(city_name, api_key)
    
    if weather_data is not None:
        print(f'Weather in {city_name}:')
        print(f'Temperature: {weather_data['main']['temp']}�C')
        print(f'Description: {weather_data['weather'][0]['description']}')
        print(f'Humidity: {weather_data['main']['h umidity']}%')
    else:
        print("Failed to retrieve weather data. Please check the city name and API key.")
if __name__ == "__main__":
    main()

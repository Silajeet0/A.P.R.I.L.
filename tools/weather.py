import asyncio
import aiohttp

async def get_weather(city: str) -> str:
    # Format city name for URLs (e.g., "New York" -> "New+York")
    formatted_city = city.replace(" ", "+")
    url = f"https://wttr.in/{formatted_city}?format=j1"
    
    # Custom headers to identify your request cleanly
    headers = {'User-Agent': 'Mozilla/5.0 (A.P.R.I.L. Companion Core)'}
    
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.get(url, timeout=5) as response:
                if response.status != 200:
                    return f"Failed to fetch weather. Server returned status: {response.status}"
                
                # Directly extract the raw data dictionary
                data = await response.json()
                
                # Navigate the JSON structure
                current = data['current_condition'][0]
                description = current['weatherDesc'][0]['value']
                temp_c = current['temp_C']
                feels_like = current['FeelsLikeC']
                humidity = current['humidity']
                wind_speed = current['windspeedKmph']
                pressure = current['pressure']
                
                weather_report = (
                    f"Current weather in {city}: {description} at {temp_c}°C "
                    f"(feels like {feels_like}°C). Humidity is at {humidity}%, "
                    f"pressure is {pressure} hPa, and wind speed is {wind_speed} km/h."
                )
                return weather_report
                
        except Exception as e:
            return f"Failed to fetch weather for {city}. Error: {e}"

if __name__ == "__main__":
    # Test on Kolkata
    print(asyncio.run(get_weather("Kolkata")))

        
import asyncio
import python_weather

async def get_weather(city:str)->str:
    async with python_weather.Client(unit=python_weather.METRIC) as client:
            try:
                weather = await client.get(city)

                weather_report = (
                     f"Current weather in {city}: "
                     f"{weather.description} at {weather.temperature}°C "
                     f"(feels like {weather.feels_like}°C). "
                     f"Humidity is at {weather.humidity}%, "
                     f"Pressure is {weather.pressure}, "
                     f"and wind speed is {weather.wind_speed} km/h, "
                     f"Amount of Precipitation: {weather.precipitation}. "
                )

                return weather_report
            except Exception as e:
                 return f"Failed to fetch weather for {city}. Error: {e}"
            
def weather_tool(city:str)->str:
     print(f"[Tool] Fetching weather data for: {city}")
     return asyncio.run(get_weather(city))

if __name__ == "__main__":
     print(weather_tool("Kolkata"))
        
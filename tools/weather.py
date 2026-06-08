import asyncio
import python_weather

async def get_weather(city:str)->str:
    async with python_weather.Client(unit=python_weather.METRIC) as client:
            try:
                weather = await client.get(city)

                weather_report = (
                     f"Current weather in {city}: "
                     f"{weather.description} at {weather.temperature} degrees C "
                     f"(feels like {weather.feels_like} degrees C). "
                     f"Humidity is at {weather.humidity} percent, "
                     f"Pressure is {weather.pressure}, "
                     f"and wind speed is {weather.wind_speed} kilometers per hour, "
                     f"Amount of Precipitation: {weather.precipitation}. "
                )

                return weather_report
            except Exception as e:
                 return f"Failed to fetch weather for {city}. Error: {e}"

if __name__ == "__main__":
     print(asyncio.run(get_weather("Kolkata")))
        
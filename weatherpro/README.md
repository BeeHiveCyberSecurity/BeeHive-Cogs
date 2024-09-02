# WeatherPro Cog

WeatherPro is a powerful cog for the Red Discord bot that provides detailed weather information, forecasts, and historical data for any location in the United States using ZIP codes. This cog is perfect for planning events, travel, or just staying informed about the weather in your area.

## Features

- **Current Weather**: Get the current weather conditions for any ZIP code.
- **Forecast**: Fetch future weather forecasts.
- **Historical Data**: Access historical weather data.
- **Weather Alerts**: Receive severe and extreme weather alerts.
- **Heat Alerts**: Get notified about dangerously hot temperatures.
- **Customizable**: Set your ZIP code for personalized weather queries.

>[!NOTE]
>The **[weatherpro](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/weatherpro)** cog relies on pre-mapped location information that from time to time, may be inaccurate. If you feel the conditions shown in this cog are, out-of-parity with the conditions you're experiencing in real life, you should [open an issue](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/issues/new?assignees=&labels=enhancement%2C+good+first+issue&projects=&template=location-review.md&title=%28Location+review%29) to ask us to review our location mapped for your zip code.

## Commands

### `[p]weather forecast [zip_code]`
Fetch the future weather forecast for the specified ZIP code. If no ZIP code is provided, it will use the ZIP code set in your profile.

### `[p]weatherset zip [zip_code]`
Set your ZIP code for personalized weather queries. This ZIP code will be used for future weather commands if no ZIP code is specified.

## Installation

To install the WeatherPro cog, use the following commands:

1. Add the BeeHive-Cogs repository to your Red bot:
   ```
   [p]repo add BeeHive-Cogs https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs
   ```

2. Install the WeatherPro cog from the BeeHive-Cogs repository:
   ```
   [p]cog install BeeHive-Cogs weatherpro
   ```

3. Load the WeatherPro cog:
   ```
   [p]load weatherpro
   ```

4. Set your ZIP code for personalized weather queries:
   ```
   [p]weatherset zip [your_zip_code]
   ```

Now you are ready to use the WeatherPro cog to get detailed weather information, forecasts, and alerts!

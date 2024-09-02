# WeatherPro

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

# Commands

## weather
 - Usage: `[p]weather `

Fetch current and upcoming conditions, search and explore hundreds of weather-focused words, check alert statistics across the country, and fetch information on observation stations and radar installations

### weather forecast
 - Usage: `[p]weather forecast [zip_code=None] `
 - Checks: `server_only`

Fetch your future forecast

> ### zip_code: str = None
> ```
> A single word, if not using slash and multiple words are necessary use a quote e.g "Hello world".
> ```
### weather now
 - Usage: `[p]weather now [zip_code=None] `

Check current conditions and alerts, specify a zip for conditions at that location

> ### zip_code: str = None
> ```
> A single word, if not using slash and multiple words are necessary use a quote e.g "Hello world".
> ```
### weather stats
 - Usage: `[p]weather stats `

Show statistics about weather feature usage

### weather alerts
 - Usage: `[p]weather alerts `
 - Checks: `server_only`

Shows a statistical summary of active weather alerts

### weather stations
 - Usage: `[p]weather stations `
 - Checks: `server_only`

Explore US weather observation stations

### weather radars
 - Usage: `[p]weather radars `
 - Checks: `server_only`

Explore US weather radar installations

### weather glossary
 - Usage: `[p]weather glossary [search_term] `
 - Checks: `server_only`

Show a glossary, or specify a word to search

> ### search_term: str = None
> ```
> A single word, if not using slash and multiple words are necessary use a quote e.g "Hello world".
> ```
### weather records
 - Usage: `[p]weather records `

Show historical weather records

### weather profile
 - Usage: `[p]weather profile `

View your weather profile

## weatherset
 - Usage: `[p]weatherset `

Configure settings and features of weather

### weatherset freezealerts
 - Usage: `[p]weatherset freezealerts `
 - Cooldown: `1 per 900.0 seconds`

Toggle freeze alerts for your saved location

### weatherset heatalerts
 - Usage: `[p]weatherset heatalerts `
 - Cooldown: `1 per 900.0 seconds`

Toggle heat alerts for your saved location

### weatherset severealerts
 - Usage: `[p]weatherset severealerts `
 - Cooldown: `1 per 900.0 seconds`

Toggle severe alerts for your saved location

### weatherset zip
 - Usage: `[p]weatherset zip <zip_code> `

Set your zip code for queries

> ### zip_code: str
> ```
> A single word, if not using slash and multiple words are necessary use a quote e.g "Hello world".
> ```


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

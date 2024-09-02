# About this repo
Red is a free, self-hostable, open-source Discord bot that can be used in growing Discord communities to help personalize and modularize server management, moderation, games, and more. 

This repo contains cogs built for Red that can help keep your community safer, in many cases for free. 

## Adding the repo
To add this repo to your Red bot, use the command

```[p]repo add BeeHive-Cogs https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs```

## Adding cogs to your bot
To install cogs from this repo to your Red instance, use the command

```[p]cog install BeeHive-Cogs (cogname)```

then load the newly installed cog with

```[p]load (cogname)```

## Cog directory
- **[weatherpro](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/weatherpro)** - Access detailed weather information, forecasts, and historical data for any location in the United States using ZIP codes. Perfect for planning events, travel, or just staying informed about the weather in your area. `[p]weather`, `[p]weatherset`.
>[!NOTE]
>The [weatherpro](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/weatherpro) cog relies on pre-mapped location information that from time to time, may be inaccurate. If you feel the conditions shown in this cog are, out-of-parity with the conditions you're experiencing in real life, you should [open an issue](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/issues/new/choose) to ask us to review our location mapped for your zip code.

- **[ping](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/ping)** - A nice, functional ping and SpeedTest tool combined. One command, no fuss - `[p]ping`
- **[nicknamemanagement](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/nicknamemanagement)** - Help manage unruly, unsightly, and otherwise annoying nicknames/screennames in your server. A dehoister on steroids, that dislikes anything that isn't alphanumeric.
- **[cloudflare](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/cloudflare)** - Utilize a multitude of advanced Cloudflare tools thru Discord, including the Cloudflare URL Scanner. For the bot owner, unlock the ability to interact with multiple Cloudflare products you utilize thru your Red-DiscordBot instance.
- **[virustotal](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/virustotal)** - Utilize the VirusTotal API and a `free` VirusTotal API Key to analyze files and URLs for malicious content.
- **[urlscan](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/urlscan)** - Utilize the URLScan.io API and a `free` URLScan API Key to analyze URL's for safety and/or security, or enable `[p]urlscan autoscan` to keep your chat safer on autopilot.
- **[antiphishing](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/antiphishing)** - Passively detect and remove malicious websites sent in your server's chats. Always on, always watchful. `(recommended)`
- **[products](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/products)** - Cog made for primarily our server to help us deliver information on our products to inquisitive users. `(incomplete)`
- **[stripeidentity](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/stripeidentity)** - Intake and verify drivers licenses, passports, state ID's, and more using Stripe Identity thru your Red-DiscordBot instance to enforce age restrictions in your adults-only server. Requires a Stripe account in good standing with access to Stripe Identity. Costs 50c/$1.50 per verification.
- **[skysearch](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/skysearch)** - Interactive features to let you explore and search for aircraft by their registrations, squawks, ICAO 24-bit addresses, and more, as well as fetch information about airports like locations, photos, forecasts, and more. Start SkySearch once installed using `[p]aircraft` or `[p]airport`, respectively.
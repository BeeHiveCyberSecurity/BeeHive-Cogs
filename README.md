# Welcome to BeeHive-Cogs

## About this repo
Red is a free, self-hostable, open-source Discord bot that can be used in growing Discord communities to help personalize and modularize server management, moderation, games, and more. 

This repository contains cogs that can help equip your Red instance with advanced features that safeguard your community, and improve your member's server experience.

## Adding the repo
Before you can install our cogs, you need to add our repo to your instance so it can find, our cogs by name. To do so, run the following command.

```
[p]repo add BeeHive-Cogs https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs
```

When you run this command, Red may give you a warning about installing third party cogs. If you're presented with this, you'll need to respond in chat with "I agree". 

We'll provide a, relatively same-in-spirit disclaimer below.

>[!CAUTION]
>**Installing third-party cogs can increase resource utilization, create security risks, reduce system stability, and otherwise severely degrade usability of your bot, especially in resource-restricted environments.** 
>
>**Only install cogs from sources that you trust. The creator of Red and its community have no responsibility for any potential damage that the content of 3rd party repositories might cause.** 


## Public cogs
Our public cogs are the cogs we make that do, assorted things. Maybe you'll find them useful - or maybe not. 

### [weatherpro](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/weatherpro)

Access detailed weather information, forecasts, and historical data for any location in the United States using ZIP codes. Perfect for planning events, travel, or just staying informed about the weather in your area. `[p]weather`, `[p]weatherset`.


```
[p]cog install BeeHive-Cogs weatherpro
```
```
[p]load weatherpro
```


### [ping](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/ping)

A nice, functional ping-and-speedtest cog that shows your host latency, transit latency, download speed, and upload speed in a neat, orderly, no-frills embed. If your bot is hosted on a poor quality connection, includes a special offer when detected. `[p]ping`

```
[p]cog install BeeHive-Cogs ping
```
```
[p]load ping
```

### [names](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/names)

Help manage unruly, unsightly, and otherwise annoying nicknames/screennames in your server. Purify and normalize visually obnoxious names manually, or enable automatic cleanups to keep your server tidy. `[p]nickname`.

```
[p]cog install BeeHive-Cogs names
```
```
[p]load names
```

### [antiphishing](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/antiphishing)

Passively detect and remove known malicious websites sent in your server's chats. `[p]antiphishing`

```
[p]cog install BeeHive-Cogs antiphishing
```
```
[p]load antiphishing
```

### [skysearch](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/skysearch)

Interactive features to let you explore and search for aircraft by their registrations, squawks, ICAO 24-bit addresses, and more, as well as fetch information about airports like locations, photos, forecasts, and more. `[p]aircraft`, `[p]airport`.

```
[p]cog install BeeHive-Cogs skysearch
```
```
[p]load skysearch
```

### [disclaimers](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/disclaimers)

Set up and manage pre-defined disclaimers that attach to users of particular significance, like lawyers, financial advisors, or other professions where a disclaimer may be warranted as a responsible disclosure. `[p]disclaimers`.

```
[p]cog install BeeHive-Cogs disclaimers
```
```
[p]load disclaimers
```

### [serverinfo](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/serverinfo)

Provides detailed information about your Discord server, including member statistics, channel counts, role information, and more. Useful to keep track of various server metrics and check if the server is configured, relatively, correctly. `[p]serverinfo`.

```
[p]cog install BeeHive-Cogs serverinfo
```
```
[p]load serverinfo
```

### [invites](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/invites)

Manage and track invite links for your Discord server. This cog allows you to see who invited whom, track the number of uses for each invite link, and generate new invite links with specific settings. Useful for community growth and moderation. `[p]invites`.

```
[p]cog install BeeHive-Cogs invites
```
```
[p]load invites
```



### [products](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/products)

Cog made for primarily our server to help us deliver information on our products to inquisitive users. `(incomplete)`

## Brand cogs
Brand cogs are cogs we make that are intended to integrate other third party services primarily with your, Red instance. Red is a powerful tool when correctly equipped, and we hope these cogs help extend your Red-bot's capabilities.

>[!TIP]
>Unless otherwise specified, brand cogs are not authored, audited, or endorsed by the brands and tools that they interact with.
>These are made open-effort and open-source to extend the functionality of Red-DiscordBot, not to imbibe an endorsement of any one specific brand.
>If you choose to use these in potentially sensitive environments, this is the disclaimer that indicates you do so at your own risk and liability.

### [cloudflare](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/cloudflare)

Utilize a multitude of advanced Cloudflare tools thru Discord, including the Cloudflare URL Scanner. For the bot owner, unlock the ability to interact with multiple Cloudflare products you utilize thru your Red-DiscordBot instance.

```
[p]cog install BeeHive-Cogs cloudflare
```
```
[p]load cloudflare
```

### [virustotal](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/virustotal)

Utilize the VirusTotal API with a free API key to scan and analyze files for potential threats and malicious content. `[p]virustotal`.

```
[p]cog install BeeHive-Cogs virustotal
```
```
[p]load virustotal
```

### [urlscan](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/urlscan)

Leverage the power of the URLScan.io API with a `free` URLScan API Key to evaluate URLs for safety and security. Enable `[p]urlscan autoscan` to automatically monitor and protect your chat from potentially harmful links. `[p]urlscan`.

```
[p]cog install BeeHive-Cogs urlscan
```
```
[p]load urlscan
```

### [stripeidentity](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/stripeidentity)

Utilize Stripe Identity through your Red-DiscordBot instance to intake and verify various forms of identification, including driver's licenses, passports, and state IDs. This feature is ideal for enforcing age restrictions in adult-only servers. Note that a Stripe account in good standing with access to Stripe Identity is required. Verification costs are $0.50 or $1.50 per verification. `[p]agecheck`, `[p]identitycheck`.

```
[p]cog install BeeHive-Cogs stripeidentity
```
```
[p]load stripeidentity
```




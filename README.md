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

# About these cogs
- [virustotal](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/virustotal) - Utilize the VirusTotal API and a (free) VirusTotal account to analyze files for malware and get back multiple vendor verdicts at once. Very useful in communities where people are naturally irresponsible and will run nearly anything sent to them without a second thought.
- [antiphishing](https://github.com/BeeHiveCyberSecurity/BeeHive-Cogs/tree/main/antiphishing) - Help detect and remove malicious website links sent in your Discord server. By default comes configured to notify, but can kick, ban, and more to protect on your behalf. Takes advantage of our curated threat intelligence to update known malicious links every 10 minutes from our blocklist.
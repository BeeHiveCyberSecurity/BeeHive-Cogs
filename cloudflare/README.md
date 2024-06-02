# Cloudflare
This is a cog for Red-Discordbot that makes it easy to interact with services and tools that Cloudflare provides, thru your Discord bot.

[Leave a donation to support development efforts in any amount that works for you!](https://donate.stripe.com/eVag0y2kI9BI36McNa)

# Configuration
> [!IMPORTANT]
> You must set a `cloudflare` `api_key`, `email`, `account_id`, `zone_id`, and `bearer_token` within your Red instance.
> `api_key` is your **Cloudflare Global API Key**. This is the key you use to query Cloudflare public/semi-public resources, period.
> `email` is the email attached to your **Cloudflare Account**, aka, the email you used to sign in.
> `account_id` is listed on every domain's initial dashboard page. We recommend you choose your "primary" domain's `account_id`, if you plan to take advantage of all of the features the cog supports.
> `zone_id` is above the `account_id`, same location. We recommend you choose your "primary" domain's `zone_id`, if you plan to manage it. You can rotate your `zone_id` to manage different domains under your  Cloudflare account, if you have multiple.
> `bearer_token` is your **Cloudflare User API Key** you'll create by going [here](https://dash.cloudflare.com/profile/api-tokens). This needs it's own disclaimer.
>
> The command to set these individual values is `[p]set api cloudflare KEYTYPE YOURKEYHERE`
### Cloudflare  integration

**Price** - **FREE** with respect to rate limits

**API in use** - [Cloudflare](https://developers.cloudflare.com/api/)

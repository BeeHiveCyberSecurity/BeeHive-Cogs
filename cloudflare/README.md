# Cloudflare
This is a cog for Red-Discordbot that makes it easy to interact with services and tools that Cloudflare provides, thru your Discord bot.

[Leave a donation to support development efforts in any amount that works for you!](https://donate.stripe.com/eVag0y2kI9BI36McNa)

# Configuration
> [!IMPORTANT]
> You must set a `cloudflare` `api_key`, `email`, `account_id`, `zone_id`, and `bearer_token` within your Red instance.
>
> `api_key` is your **Cloudflare Global API Key**. This is the key you use to query Cloudflare public/semi-public resources, period.
>
> `email` is the email attached to your **Cloudflare Account**, aka, the email you used to sign in.
>
> `account_id` is listed on every domain's initial dashboard page. We recommend you choose your "primary" domain's `account_id`, if you plan to take advantage of all of the features the cog supports.
>
> `zone_id` is above the `account_id`, same location. We recommend you choose your "primary" domain's `zone_id`, if you plan to manage it. You can rotate your `zone_id` to manage different domains under your  Cloudflare account, if you have multiple.
>
> `bearer_token` is your **Cloudflare User API Key** you'll create by going [here](https://dash.cloudflare.com/profile/api-tokens). This needs it's own disclaimer.
>
> The command to set these individual values is `[p]set api cloudflare KEYTYPE YOURKEYHERE`


> [!CAUTION]
> **Take the security and safety of your Cloudflare profile, and Discord account, seriously - and consider your own threat models before using this cog. We recommend that regardless of if you are self-hosting your Red instance, or using a VPS, you should install and test paid endpoint protection software. If a threat actor gains access to your Discord account, they will have access to the values set here. If a threat actor gains access to the machine running your bot, they may be able to access and abuse your keys. If you host multiple domains thru your Cloudflare, a threat actor could use these stolen credentials to do serious damage to these domains, up-to-and-including disconnecting email and DNS services.**

>[!WARNING]
> Cloudflare's permission controls are extremely granular and customizable. If you're new to the Cloudflare ecosystem, or only wishing to use Intelligence and URL Scanning features, you can use the template "Read Cloudflare Radar data" safely. However, other features of the cog (like R2, Images, and Email Routing) won't work whatsoever - this may be exactly what you want, for your own security's sake.
>
> **EXERCISE EXTREME CARE WHEN CREATING AN API KEY WITH DANGEROUS PERMISSION LEVELS**

### Cloudflare  integration

**Price** - **FREE** with respect to rate limits

**API in use** - [Cloudflare](https://developers.cloudflare.com/api/)

# Commands

# images
 - Usage: `[p]images `
 - Restricted to: `BOT_OWNER`

Cloudflare Images provides an end-to-end solution to build and maintain your image infrastructure from one API. Learn more at https://developers.cloudflare.com/images/

## images delete
 - Usage: `[p]images delete <image_id> `
 - Restricted to: `BOT_OWNER`

Delete an image from Cloudflare Images by its ID.

## images list
 - Usage: `[p]images list `
 - Restricted to: `BOT_OWNER`

List available images.

## images info
 - Usage: `[p]images info <image_id> `
 - Restricted to: `BOT_OWNER`

Get information about a specific image.

## images stats
 - Usage: `[p]images stats `
 - Restricted to: `BOT_OWNER`

Fetch Cloudflare Images usage statistics.

## images upload
 - Usage: `[p]images upload `
 - Restricted to: `BOT_OWNER`

Upload an image to Cloudflare Images.

# loadbalancing
 - Usage: `[p]loadbalancing `

Cloudflare Load Balancing distributes traffic across your servers, which reduces server strain and latency and improves the experience for end users. Learn more at https://developers.cloudflare.com/load-balancing/

## loadbalancing patch
 - Usage: `[p]loadbalancing patch <load_balancer_id> <key> <value> `
 - Restricted to: `BOT_OWNER`

Update the settings of a specific load balancer.

## loadbalancing create
 - Usage: `[p]loadbalancing create <name> <description> <default_pools> <country_pools> <pop_pools> <region_pools> <proxied> <ttl> <adaptive_routing> <failover_across_pools> <fallback_pool> <location_strategy_mode> <location_strategy_prefer_ecs> <random_steering_default_weight> <random_steering_pool_weights> <steering_policy> <session_affinity> <session_affinity_ttl> `
 - Restricted to: `BOT_OWNER`

Create a new load balancer for a specific zone.

## loadbalancing info
 - Usage: `[p]loadbalancing info <load_balancer_id> `
 - Restricted to: `BOT_OWNER`

Get information about a specific load balancer by its ID.

## loadbalancing list
 - Usage: `[p]loadbalancing list `
 - Restricted to: `BOT_OWNER`

Get a list of load balancers for a specific zone.

## loadbalancing delete
 - Usage: `[p]loadbalancing delete <load_balancer_id> `
 - Restricted to: `BOT_OWNER`

Delete a load balancer by its ID.

# dnssec
 - Usage: `[p]dnssec `

DNSSEC info

## dnssec delete
 - Usage: `[p]dnssec delete `
 - Restricted to: `BOT_OWNER`

Delete DNSSEC on the currently set Cloudflare zone

## dnssec status
 - Usage: `[p]dnssec status `
 - Restricted to: `BOT_OWNER`

Get the current DNSSEC status and config for a specific zone.

# keystore
 - Usage: `[p]keystore `
 - Restricted to: `BOT_OWNER`

Fetch keys in use for development purposes only

## keystore zoneid
 - Usage: `[p]keystore zoneid `
 - Restricted to: `BOT_OWNER`

Fetch the current Cloudflare zone ID

## keystore accountid
 - Usage: `[p]keystore accountid `
 - Restricted to: `BOT_OWNER`

Fetch the current Cloudflare account ID

## keystore bearertoken
 - Usage: `[p]keystore bearertoken `
 - Restricted to: `BOT_OWNER`

Fetch the current Cloudflare bearer token

## keystore apikey
 - Usage: `[p]keystore apikey `
 - Restricted to: `BOT_OWNER`

Fetch the current Cloudflare API key

## keystore email
 - Usage: `[p]keystore email `
 - Restricted to: `BOT_OWNER`

Fetch the current Cloudflare email

# botmanagement
 - Usage: `[p]botmanagement `

Cloudflare bot solutions identify and mitigate automated traffic to protect your domain from bad bots. Learn more at https://developers.cloudflare.com/bots/

## botmanagement get
 - Usage: `[p]botmanagement get `
 - Restricted to: `BOT_OWNER`

Get the current bot management config from Cloudflare.

## botmanagement update
 - Usage: `[p]botmanagement update <setting> <value> `
 - Restricted to: `BOT_OWNER`

Update a specific bot management setting.

# zones
 - Usage: `[p]zones `

Cloudflare command group.

## zones get
 - Usage: `[p]zones get `
 - Restricted to: `BOT_OWNER`

Get the list of zones from Cloudflare.

# intel
 - Usage: `[p]intel `

Cloudforce One packages the vital aspects of modern threat intelligence and operations to make organizations smarter, more responsive, and more secure. Learn more at https://www.cloudflare.com/application-services/products/cloudforceone/

## intel whois
 - Usage: `[p]intel whois <domain> `

Query WHOIS information for a given domain.

## intel asn
 - Usage: `[p]intel asn <asn> `

Fetch and display ASN intelligence from Cloudflare.

## intel domainhistory
 - Usage: `[p]intel domainhistory <domain> `

Fetch and display category and domain history.

## intel ip
 - Usage: `[p]intel ip <ip> `

Query intelligence on a public IP address.

## intel domain
 - Usage: `[p]intel domain <domain> `

Query Cloudflare API for domain intelligence.

## intel subnets
 - Usage: `[p]intel subnets <asn> `

Fetch and display ASN subnets intelligence from Cloudflare.

# urlscanner
 - Usage: `[p]urlscanner `

With Cloudflare’s URL Scanner, you have the ability to investigate the details of a domain, IP, URL, or ASN. Cloudflare’s URL Scanner is available in the Security Center of the Cloudflare dashboard, Cloudflare Radar and the Cloudflare API.<br/><br/>Learn more at https://developers.cloudflare.com/radar/investigate/url-scanner/

## urlscanner scan
 - Usage: `[p]urlscanner scan <url> `

Scan a URL using Cloudflare URL Scanner and return the verdict.

## urlscanner create
 - Usage: `[p]urlscanner create <url> `

Start a new scan for the provided URL.

## urlscanner screenshot
 - Usage: `[p]urlscanner screenshot <scan_id> `

Get the screenshot of a scan by its scan ID

## urlscanner search
 - Usage: `[p]urlscanner search <query> `

Search for URL scans by date and webpage requests.

## urlscanner results
 - Usage: `[p]urlscanner results <scan_id> `

Get the result of a URL scan by its ID.

## urlscanner har
 - Usage: `[p]urlscanner har <scan_id> `

Fetch the HAR of a scan by the scan ID

# emailrouting
 - Usage: `[p]emailrouting `
 - Restricted to: `BOT_OWNER`

Cloudflare Email Routing is designed to simplify the way you create and manage email addresses, without needing to keep an eye on additional mailboxes. Learn more at https://developers.cloudflare.com/email-routing/

## emailrouting settings
 - Usage: `[p]emailrouting settings `
 - Restricted to: `BOT_OWNER`

Get and display the current Email Routing settings for a specific zone

## emailrouting disable
 - Usage: `[p]emailrouting disable `
 - Restricted to: `BOT_OWNER`

Disable Email Routing for the selected zone

## emailrouting records
 - Usage: `[p]emailrouting records `
 - Restricted to: `BOT_OWNER`

Get the required DNS records to setup Email Routing

## emailrouting rules
 - Usage: `[p]emailrouting rules `
 - Restricted to: `BOT_OWNER`

Manage your Email Routing rules

### emailrouting rules list
 - Usage: `[p]emailrouting rules list `
 - Restricted to: `BOT_OWNER`

Show current Email Routing rules

### emailrouting rules add
 - Usage: `[p]emailrouting rules add <source> <destination> `
 - Restricted to: `BOT_OWNER`

Add a rule to Email Routing

### emailrouting rules remove
 - Usage: `[p]emailrouting rules remove <rule_id> `
 - Restricted to: `BOT_OWNER`

Remove a rule from Email Routing

## emailrouting remove
 - Usage: `[p]emailrouting remove <email> `
 - Restricted to: `BOT_OWNER`

Remove a destination address from your Email Routing service.

## emailrouting enable
 - Usage: `[p]emailrouting enable `
 - Restricted to: `BOT_OWNER`

Enable Email Routing for the selected zone

## emailrouting add
 - Usage: `[p]emailrouting add <email> `
 - Restricted to: `BOT_OWNER`

Add a new destination address to your Email Routing service.

## emailrouting list
 - Usage: `[p]emailrouting list `
 - Restricted to: `BOT_OWNER`

List current destination addresses

# hyperdrive
 - Usage: `[p]hyperdrive `
 - Restricted to: `BOT_OWNER`

Hyperdrive is a service that accelerates queries you make to existing databases, making it faster to access your data from across the globe, irrespective of your users’ location. Learn more at https://developers.cloudflare.com/hyperdrive/

## hyperdrive patch
 - Usage: `[p]hyperdrive patch <hyperdrive_id> <changes> `
 - Restricted to: `BOT_OWNER`

Patch a specified Hyperdrive by its ID with provided changes.

## hyperdrive update
 - Usage: `[p]hyperdrive update <hyperdrive_id> <changes> `
 - Restricted to: `BOT_OWNER`

Update and return the specified Hyperdrive configuration.

## hyperdrive info
 - Usage: `[p]hyperdrive info <hyperdrive_id> `
 - Restricted to: `BOT_OWNER`

Fetch information about a specified Hyperdrive by its ID.

## hyperdrive list
 - Usage: `[p]hyperdrive list `
 - Restricted to: `BOT_OWNER`

List current Hyperdrives in the specified account

## hyperdrive delete
 - Usage: `[p]hyperdrive delete <hyperdrive_id> `
 - Restricted to: `BOT_OWNER`

Delete a Hyperdrive.

## hyperdrive create
 - Usage: `[p]hyperdrive create <name> <password> <database> <host> <port> <scheme> <user> <caching_disabled> <max_age> <stale_while_revalidate> `
 - Restricted to: `BOT_OWNER`

Create a new Hyperdrive

# r2
 - Usage: `[p]r2 `
 - Restricted to: `BOT_OWNER`

Cloudflare R2 Storage allows developers to store large amounts of unstructured data without the costly egress bandwidth fees associated with typical cloud storage services. <br/><br/>Learn more at https://developers.cloudflare.com/r2/

## r2 stash
 - Usage: `[p]r2 stash <bucket_name> `
 - Restricted to: `BOT_OWNER`

Upload a file to the specified R2 bucket

## r2 info
 - Usage: `[p]r2 info <bucket_name> `
 - Restricted to: `BOT_OWNER`

Get info about an R2 bucket

## r2 delete
 - Usage: `[p]r2 delete <bucket_name> `
 - Restricted to: `BOT_OWNER`

Delete a specified R2 bucket

## r2 recycle
 - Usage: `[p]r2 recycle <bucket_name> <file_name> `
 - Restricted to: `BOT_OWNER`

Delete a file by name from an R2 bucket

## r2 fetch
 - Usage: `[p]r2 fetch <bucket_name> <file_name> `
 - Restricted to: `BOT_OWNER`

Fetch a file from an R2 bucket

## r2 create
 - Usage: `[p]r2 create <name> <location_hint> `
 - Restricted to: `BOT_OWNER`

Create a new R2 bucket<br/><br/>**Valid location hints**<br/><br/>**apac** - Asia-Pacific<br/>**eeur** - Eastern Europe<br/>**enam** - Eastern North America<br/>**weur** - Western Europe<br/>**wnam** - Western North America
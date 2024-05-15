# SkySearch
SkySearch is a cog for Red-Discordbot that makes getting information about airplanes, helicopters, blimps, drones, and nearly any other airborne item that can be tracked via radio formats like ADS-B, MLAT, and others, as well as airport information, runway status and related information, airport weather forecasts, and more.

[Leave a donation to support development efforts in any amount that works for you!](https://donate.stripe.com/eVag0y2kI9BI36McNa)

# Configuration
Before SkySearch functions properly on your own instance of Red, you'll need to set a few specific API keys to make sure all data is accessible to the cog as designed. Since Red is, inherrently, free, we've tried to target as many "Free" or "Freemium" API's here as possible compared to adding paid-only API's. That being said, some of these API's can be somewhat complex to interact with and actually configure. Ideally, any of these are optional - but, then this cog will be somewhat boring, less technical, you know the deal.

### Google Maps integration

**Price** - **FREE** for up to 28,500 maploads per month (919/day in a 31 day month)

**Function** - The cog will fetch down a static map image of the airport queried using `airport about`. 

**Requirement** - You must set a `googlemaps` `api_key` within your Red instance.

**API in use** - [Maps Static API](https://developers.google.com/maps/documentation/maps-static)

**Command** - `[p]set api googlemaps api_key YOURAPIKEYHERE`


### airportdb.io integration

**Price** - **FREE** for up to 5,000 queries / month

**Function** - The cog will fetch information about airports, like runway details, using `airport runway`

**Requirement** - You must set a `airportdbio` `api_token` within your Red instance.

**API in use** - [airportdb.io api](https://airportdb.io/#)

**Command** - `[p]set api airportdbio api_token YOURAPITOKENHERE`

# Commands
# aircraft
 - Usage: `[p]aircraft `
 - Aliases: `skysearch`
 - Checks: `server_only`

Summon the aircraft panel

## aircraft squawk
 - Usage: `[p]aircraft squawk <squawk_value> `
 - Checks: `server_only`

Get information about an aircraft by its squawk code.

## aircraft stats
 - Usage: `[p]aircraft stats `
 - Checks: `server_only`

Get statistics about SkySearch and the data used here

## aircraft callsign
 - Usage: `[p]aircraft callsign <callsign> `
 - Checks: `server_only`

Get information about an aircraft by its callsign.

## aircraft pia
 - Usage: `[p]aircraft pia `
 - Checks: `server_only`

View live aircraft using private ICAO addresses

## aircraft showalertchannel
 - Usage: `[p]aircraft showalertchannel `
 - Checks: `server_only`

Show alert task status and output if set

## aircraft alertchannel
 - Usage: `[p]aircraft alertchannel <channel> `
 - Checks: `server_only`

Set a channel to send emergency squawk alerts to.

## aircraft radius
 - Usage: `[p]aircraft radius <lat> <lon> <radius> `
 - Checks: `server_only`

Get information about aircraft within a specified radius.

## aircraft scroll
 - Usage: `[p]aircraft scroll `
 - Checks: `server_only`

Scroll through available planes.

## aircraft reg
 - Usage: `[p]aircraft reg <registration> `
 - Checks: `server_only`

Get information about an aircraft by its registration.

## aircraft military
 - Usage: `[p]aircraft military `
 - Checks: `server_only`

Get information about military aircraft.

## aircraft type
 - Usage: `[p]aircraft type <aircraft_type> `
 - Checks: `server_only`

Get information about aircraft by its type.

## aircraft ladd
 - Usage: `[p]aircraft ladd `
 - Checks: `server_only`

Get information on LADD-restricted aircraft

## aircraft icao
 - Usage: `[p]aircraft icao <hex_id> `
 - Checks: `server_only`

Get information about an aircraft by its 24-bit ICAO Address

## aircraft export
 - Usage: `[p]aircraft export <search_type> <search_value> <file_format> `
 - Checks: `server_only`

Search aircraft by ICAO, callsign, squawk, or type and export the results.

## aircraft autoicao
 - Usage: `[p]aircraft autoicao [state=None] `
 - Checks: `server_only`

Enable or disable automatic ICAO lookup.

# airport
 - Usage: `[p]airport `
 - Aliases: `groundsearch`
 - Checks: `server_only`

Summon SkySearch ground search panel

## airport runway
 - Usage: `[p]airport runway <code> `
 - Checks: `server_only`

Query runway information by ICAO code.

## airport about
 - Usage: `[p]airport about [code=None] `
 - Checks: `server_only`

Query airport information by ICAO or IATA code.
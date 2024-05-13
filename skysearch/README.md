# SkySearch
SkySearch is a cog for Red-Discordbot that makes getting information about airplanes, helicopters, blimps, drones, and nearly any other airborne item that can be tracked via radio formats like ADS-B, MLAT, and others. 

[Leave a donation to support development efforts in any amount that works for you!](https://donate.stripe.com/eVag0y2kI9BI36McNa)

# Commands
## skysearch
 - Usage: `!skysearch `

Summon the SkySearch panel

## skysearch squawk
 - Usage: `!skysearch squawk <squawk_value> `

Get information about an aircraft by its squawk code.

## skysearch pia
 - Usage: `!skysearch pia `

View live aircraft using private ICAO addresses

## skysearch showalertchannel
 - Usage: `!skysearch showalertchannel `

Show alert task status and output if set

## skysearch type
 - Usage: `!skysearch type <aircraft_type> `

Get information about aircraft by its type.

## skysearch military
 - Usage: `!skysearch military `

Get information about military aircraft.

## skysearch ladd
 - Usage: `!skysearch ladd `

Get information on LADD-restricted aircraft

## skysearch alertmention
 - Usage: `!skysearch alertmention <mention> `

Set a specific type of mention or roles to be tagged when a squawk alert.

## skysearch reg
 - Usage: `!skysearch reg <registration> `

Get information about an aircraft by its registration.

## skysearch stats
 - Usage: `!skysearch stats `

Get statistics about SkySearch and the data used here

## skysearch scroll
 - Usage: `!skysearch scroll `

Scroll through available planes.

## skysearch autoicao
 - Usage: `!skysearch autoicao [state=None] `
 - Checks: `server_only`

Enable or disable automatic ICAO lookup.

## skysearch icao
 - Usage: `!skysearch icao <hex_id> `

Get information about an aircraft by its 24-bit ICAO Address

## skysearch alertchannel
 - Usage: `!skysearch alertchannel <channel> `

Set a channel to send emergency squawk alerts to.

## skysearch export
 - Usage: `!skysearch export <search_type> <search_value> <file_format> `

Search aircraft by ICAO, callsign, squawk, or type and export the results.

## skysearch radius
 - Usage: `!skysearch radius <lat> <lon> <radius> `

Get information about aircraft within a specified radius.

## skysearch callsign
 - Usage: `!skysearch callsign <callsign> `

Get information about an aircraft by its callsign.
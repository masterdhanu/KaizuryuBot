import os
from KaizuryuBot import telethn as tbot
from geopy.geocoders import Nominatim
from KaizuryuBot.events import register
from KaizuryuBot import *
from telethon import *
from telethon.tl import *

GMAPS_LOC = "https://maps.googleapis.com/maps/api/geocode/json"


@register(pattern="^/gps (.*)")
async def _(event):
    args = event.pattern_match.group(1)

    try:
        geolocator = Nominatim(user_agent="SkittBot")
        location = args
        geoloc = geolocator.geocode(location)
        longitude = geoloc.longitude
        latitude = geoloc.latitude
        gm = f"https://www.google.com/maps/search/{latitude},{longitude}"
        await tbot.send_file(
            event.chat_id,
            file=types.InputMediaGeoPoint(
                types.InputGeoPoint(float(latitude), float(longitude))
            ),
        )
        await event.reply(f"Open with: [🌏Google Maps]({gm})", link_preview=False)
    except Exception as e:
        print(e)
        await event.reply("I can't find that")


__help__ = """
Sends you the gps location of the given query...

 ❍ /gps <location>*:* Get gps location.
"""

__mod_name__ = "Gᴘs"

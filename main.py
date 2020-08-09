import requests
import json
import datetime

#music 741789363083542608
#general 693968832859209802

channel_id = 693968832859209802
token = os.getenv("discord_token")

run_lag = datetime.datetime.now() - datetime.timedelta(minutes=15)

def get_messages(snowflake):
    if snowflake != "":
        param = f"?before={snowflake}"
    else:
        param = ""
    base_url = f"https://discord.com/api/channels/{channel_id}/messages{param}"
    r = requests.get(base_url, headers={'Authorization': f'Bot {token}'}).text
    messages = json.loads(r)
    return messages

snowflake = ""

spotify_links = []

more_messages = True
while more_messages == True:
    messages = get_messages(snowflake)
    snowflake = messages[-1].get("id")
    for message in messages:
        timestamp = datetime.datetime.strptime(message.get("timestamp"), "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
        if timestamp > run_lag:
            if "open.spotify.com/track" in message.get("content"):
                spotify_links.append(message.get("content"))
        else:
            more_messages = False
            break

spotify_links
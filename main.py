import requests
import datetime
import json
import time

#music 741789363083542608
#general 693968832859209802

channel_id = "741789363083542608"
playlist_uri = "3pKbOOCaeOEkciDQoLShOD"
discord_token = os.getenv("discord_token")
spotify_client_id = os.getenv("SPOTIFY_CLIENT_ID")
spotify_client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")



def get_messages(snowflake):
    if snowflake != "":
        param = f"?before={snowflake}"
    else:
        param = ""
    base_url = f"https://discord.com/api/channels/{channel_id}/messages{param}"
    r = requests.get(base_url, headers={'Authorization': f'Bot {discord_token}'}).text
    messages = json.loads(r)
    return messages


# convert extracted Spotify URL's into URI's which are used to add songs to a Spotify playlist
def song_url_to_uri(spotify_links):
    uri_links = []
    for link in spotify_links:
        link = "spotify:track:" + link.split("/")[-1].split("?")[0]
        uri_links.append(link)
    return uri_links


def spotify_refresh_token(refresh_token):
    data = {
        "client_id": spotify_client_id,
        "client_secret": spotify_client_secret,
        "grant_type":"refresh_token",
        "refresh_token":refresh_token
        }
    resp = requests.post("https://accounts.spotify.com/api/token", data = data).content
    access_token_resp = json.loads(resp)
    access_token = access_token_resp.get("access_token")
    return access_token


def get_playlist_songs(access_token):
    headers = {"Authorization": f"Bearer {access_token}",}
    response = requests.get(f"https://api.spotify.com/v1/playlists/{playlist_uri}", headers=headers)
    playlist = json.loads(response.content).get("tracks").get("items")

    playlist_songs = []
    for song in playlist:
        song = song.get("track").get("uri")
        playlist_songs.append(song)
    return playlist_songs


def add_to_playlist(uri_list, access_token):
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    params = (('uris', uri_list),)
    response = requests.post(f"https://api.spotify.com/v1/playlists/{playlist_uri}/tracks", headers=headers, params=params)
    return response.content


def main():
    # set datetime to check all messages newer than "x" minutes ago
    # this should be set to match the frequency this program will be run. This is used to determine how far back program should process messages
    run_lag = datetime.datetime.now() - datetime.timedelta(minutes=16)
    spotify_links = []
    snowflake = ""
    more_messages = True
    while more_messages == True:
        messages = get_messages(snowflake)
        snowflake = messages[-1].get("id")
        for message in messages:
            msg_time = datetime.datetime.strptime(message.get("timestamp"), "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=None)
            # if message is newer than lag time, check for Spotify link
            if msg_time > run_lag:
                print(message)
                # currently only set to search for songs that are linked. Will ignore other albums or playlists.
                # If albums or playlists are to be included, remove /track from URL check
                if "open.spotify.com/track" in message.get("content"):
                    # message_id contains the discord message id of the spotify link. This can be used later to add emoji to message
                    message_id = message.get("id")
                    spotify_link = message.get("content")
                    spotify_links.append(spotify_link)
            else:
                more_messages = False
                break

        # included sleep as lazy way to prevent abusing Discord API, should update to check response header content
        # https://discord.com/developers/docs/topics/rate-limits#header-format-rate-limit-header-examples
        time.sleep(1)

    # convert spotify links to UIR's which are used to add to playlist
    uri_list = song_url_to_uri(spotify_links)

    access_token = spotify_refresh_token(refresh_token)
    playlist_songs = get_playlist_songs(access_token)

    # check to see if song is already in playlist
    new_songs = []
    for uri in uri_list:
        if uri in playlist_songs:
            continue
        else:
            new_songs.append(uri)

    new_songs = ','.join(new_songs)

    if new_songs == "":
        return "No new songs were added."
    else:
        status = add_to_playlist(new_songs, access_token)
        return status
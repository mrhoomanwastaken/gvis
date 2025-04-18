import pylast
import os
from dotenv import load_dotenv
import time

def initialize_lastfm():
    # Load environment variables from .env file
    load_dotenv()

    # Retrieve API keys from environment variables
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")

    SESSION_KEY_FILE = os.path.join(os.path.expanduser("~"), ".session_key")
    network = pylast.LastFMNetwork(API_KEY, API_SECRET)

    if not os.path.exists(SESSION_KEY_FILE):
        skg = pylast.SessionKeyGenerator(network)
        url = skg.get_web_auth_url()

        print(f"Please authorize this script to access your account: {url}\n")
        import time
        import webbrowser

        webbrowser.open(url)

        while True:
            try:
                session_key = skg.get_web_auth_session_key(url)
                with open(SESSION_KEY_FILE, "w") as f:
                    f.write(session_key)
                break
            except pylast.WSError:
                time.sleep(1)
    else:
        session_key = open(SESSION_KEY_FILE).read()

    network.session_key = session_key
    return network

def scrobble_track(network, artist, title , album , duration):
    try:
        timestamp = int(time.time())  # Current timestamp in seconds
        network.scrobble(artist=artist[0], title=title , timestamp=timestamp , album=album)
        network.update_now_playing(artist=artist[0], title=title, duration=duration)
        print(f"Scrobbled: {artist[0]} - {title} - {album}")
    except pylast.WSError as e:
        print(f"Failed to scrobble: {e}")
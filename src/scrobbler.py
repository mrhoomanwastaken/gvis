import pylast
import os
from dotenv import load_dotenv
import time

def initialize_lastfm():
    # Load environment variables from .env file
    # if you steal this I will be very sad
    # so please dont steal this
    
    # Handle different paths for compiled vs uncompiled
    import sys
    if getattr(sys, 'frozen', False):
        # Running as compiled binary
        base_path = os.path.dirname(sys.executable)
        env_path = os.path.join(base_path, '.env')
    else:
        # Running as script
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(base_path, '.env')
    
    print(f"Looking for .env file at: {env_path}")
    print(f"File exists: {os.path.exists(env_path)}")
    
    load_dotenv(env_path)

    # Retrieve API keys from environment variables
    API_KEY = os.getenv("API_KEY")
    API_SECRET = os.getenv("API_SECRET")
    
    print(f"API_KEY loaded: {'Yes' if API_KEY else 'No'}")
    print(f"API_SECRET loaded: {'Yes' if API_SECRET else 'No'}")
    
    if not API_KEY or not API_SECRET:
        raise ValueError("API_KEY or API_SECRET not found in environment variables")

    SESSION_KEY_FILE = os.path.join(os.path.expanduser("~"), ".session_key")
    
    try:
        network = pylast.LastFMNetwork(API_KEY, API_SECRET)
        print("Last.fm network object created successfully")
    except Exception as e:
        print(f"Failed to create Last.fm network object: {e}")
        raise

    if not os.path.exists(SESSION_KEY_FILE):
        print("Session key file not found, starting authentication process...")
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
                print("Session key saved successfully")
                break
            except pylast.WSError as e:
                print(f"Waiting for authorization... ({e})")
                time.sleep(1)
    else:
        print("Loading existing session key...")
        try:
            with open(SESSION_KEY_FILE, "r") as f:
                session_key = f.read().strip()
            print("Session key loaded successfully")
        except Exception as e:
            print(f"Failed to read session key file: {e}")
            raise

    try:
        network.session_key = session_key
        print("Session key set on network object")
    except Exception as e:
        print(f"Failed to set session key: {e}")
        raise
        
    return network

def scrobble_track(network, artist, title , album , duration):
    try:
        #last fm does not like scrobbling multiple artists and will log the artist as all of them if we just pass in artist[0]
        # so we need to split the artist string and take the first one
        # This formatting might be exclusive to youtube music
        fm_artist = artist[0].split(" & ")[0].split(", ")[0]
        timestamp = int(time.time())  # Current timestamp in seconds
        network.scrobble(artist=fm_artist, title=title , timestamp=timestamp , album=album)
        network.update_now_playing(artist=fm_artist, title=title, duration=duration)
        print(f"Scrobbled: {fm_artist} - {title} - {album}")
    except pylast.WSError as e:
        print(f"Failed to scrobble (WSError): {e}")
        print(f"Error type: {type(e)}")
        print(f"Error args: {e.args}")
    except Exception as e:
        print(f"Failed to scrobble (General Error): {e}")
        print(f"Error type: {type(e)}")
        print(f"Error args: {e.args}")
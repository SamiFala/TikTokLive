import asyncio
import threading

from flask_app import app

def start_flask():
    app.run()

if __name__ == "__main__":
    # Démarrer Flask dans le thread principal
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()

    # Si vous souhaitez démarrer le client TikTok au démarrage, utilisez ceci:
    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(start_tiktok_client())

    flask_thread.join()

import threading

from flask_app import run_flask, create_app

app = create_app()  # Crée l'application Flask pour Gunicorn

def start_flask():
    run_flask()

if __name__ == "__main__":
    # Démarrer Flask dans le thread principal
    flask_thread = threading.Thread(target=start_flask)
    flask_thread.start()

    # Si vous souhaitez démarrer le client TikTok au démarrage, utilisez ceci:
    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(start_tiktok_client())

    flask_thread.join()
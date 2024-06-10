import json
import requests
from ratelimiter import RateLimiter

# Constantes
SMOKE_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/C7BDBFBB7A3E/commands"
SMOKE_TWO_MACHINE_URL = "https://api.switch-bot.com/v1.0/devices/D5D127EFF039/commands"

# Rate limiter
rate_limiter = RateLimiter(max_calls=1, period=2)

# Fonction pour envoyer la commande de fumée
def send_smoke_command(url):
    body = json.dumps({
        "command": "turnOn",
        "parameter": "default",
        "commandType": "command"
    })
    headers = {
        'Authorization': 'Bearer 09f984c25288d88849a45b8dce8010b5f03104f8abc47ee87beb9031d97d6db550f2e903358b84f039b23ab3371032bc',
        'Content-Type': 'application/json'
    }
    with rate_limiter:
        try:
            response = requests.post(url, headers=headers, data=body)
            response.raise_for_status()
            print(f"Smoke command sent to {url}")
        except requests.exceptions.RequestException as err:
            print(f"Error sending smoke command: {err}")
            print(f"Response content: {response.content}")

# Fonction principale
def main():
    while True:
        command = input("Enter 'smoke' to send smoke command or 'exit' to quit: ").strip().lower()
        if command == 'smoke':
            send_smoke_command(SMOKE_MACHINE_URL)
            send_smoke_command(SMOKE_TWO_MACHINE_URL)
        elif command == 'exit':
            break
        else:
            print("Invalid command. Please enter 'smoke' or 'exit'.")

if __name__ == "__main__":
    main()
